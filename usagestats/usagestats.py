"""Bot-wide command usage stats.

Every prefix, hybrid and slash command from every cog is logged as one small row in an SQLite file in the
cog's data folder. Rows are buffered for a few seconds and written in batches, so memory use stays tiny
no matter how busy the bot is. Old rows are pruned after RETENTION_DAYS.
"""

import asyncio
import sqlite3
import time
from typing import List, Literal, Optional, Tuple

import discord
from discord.ext import tasks
from redbot.core import app_commands, commands
from redbot.core.data_manager import cog_data_path

Period = Literal["day", "week", "month", "year", "all"]
PERIOD_SECONDS = {"day": 86_400, "week": 7 * 86_400, "month": 30 * 86_400, "year": 365 * 86_400, "all": None}
PERIOD_LABEL = {"day": "last 24 hours", "week": "last 7 days", "month": "last 30 days", "year": "last 365 days", "all": "all time"}
RETENTION_DAYS = 400  # a little over a year, so "year" always has full data
FLUSH_EVERY = 15  # seconds
FLUSH_AT = 200  # rows; flush early when this many are waiting
COLOR = discord.Color.blurple()

SCHEMA = """
CREATE TABLE IF NOT EXISTS uses (
  ts INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  guild_id INTEGER,
  command TEXT NOT NULL,
  cog TEXT,
  slash INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS uses_ts ON uses (ts);
CREATE INDEX IF NOT EXISTS uses_user ON uses (user_id);
"""


def _since(period: str) -> int:
  secs = PERIOD_SECONDS.get(period)
  return 0 if secs is None else int(time.time()) - secs


class UsageStats(commands.Cog):
  """See how many people use the bot and which commands they run."""

  def __init__(self, bot):
    self.bot = bot
    self.db_path = cog_data_path(self) / "usage.sqlite3"
    self._buffer: List[Tuple[int, int, Optional[int], str, Optional[str], int]] = []
    self._lock = asyncio.Lock()

  async def cog_load(self):
    await self._run(self._init_db)
    self.flush_loop.start()

  async def cog_unload(self):
    self.flush_loop.cancel()
    await self._flush()

  # ---- database (all sqlite work runs in a thread so the bot never blocks)

  async def _run(self, fn, *args):
    return await asyncio.get_running_loop().run_in_executor(None, fn, *args)

  def _connect(self) -> sqlite3.Connection:
    conn = sqlite3.connect(str(self.db_path), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

  def _init_db(self):
    with self._connect() as conn:
      conn.executescript(SCHEMA)
      conn.execute("DELETE FROM uses WHERE ts < ?", (int(time.time()) - RETENTION_DAYS * 86_400,))

  def _write(self, rows):
    with self._connect() as conn:
      conn.executemany("INSERT INTO uses VALUES (?, ?, ?, ?, ?, ?)", rows)

  def _query(self, sql: str, params: tuple = ()):
    with self._connect() as conn:
      return conn.execute(sql, params).fetchall()

  async def _flush(self):
    async with self._lock:
      if not self._buffer:
        return
      rows, self._buffer = self._buffer, []
    await self._run(self._write, rows)

  @tasks.loop(seconds=FLUSH_EVERY)
  async def flush_loop(self):
    await self._flush()

  @flush_loop.before_loop
  async def _before_flush(self):
    await self.bot.wait_until_red_ready()

  # ---- logging

  def _log(self, user_id: int, guild_id: Optional[int], command: str, cog: Optional[str], slash: bool):
    self._buffer.append((int(time.time()), user_id, guild_id, command, cog, int(slash)))
    if len(self._buffer) >= FLUSH_AT:
      asyncio.ensure_future(self._flush())

  @commands.Cog.listener()
  async def on_command_completion(self, ctx: commands.Context):
    """Prefix commands, and hybrid commands whether run with a prefix or as slash commands."""
    cmd = ctx.command
    if cmd is None:
      return
    self._log(ctx.author.id, ctx.guild.id if ctx.guild else None, cmd.qualified_name, cmd.cog_name, ctx.interaction is not None)

  @commands.Cog.listener()
  async def on_app_command_completion(self, interaction: discord.Interaction, command):
    """Slash-only and context-menu commands (hybrid ones are already logged above)."""
    if hasattr(command, "wrapped"):  # HybridAppCommand: counted by on_command_completion
      return
    binding = getattr(command, "binding", None)
    cog = binding.qualified_name if isinstance(binding, commands.Cog) else None
    name = getattr(command, "qualified_name", None) or getattr(command, "name", "?")
    self._log(interaction.user.id, interaction.guild_id, name, cog, True)

  # ---- Red data API

  async def red_delete_data_for_user(self, *, requester, user_id: int):
    await self._flush()
    await self._run(self._query, "DELETE FROM uses WHERE user_id = ?", (user_id,))

  # ---- helpers

  def _guild_name(self, guild_id: Optional[int]) -> str:
    if guild_id is None:
      return "Direct messages"
    g = self.bot.get_guild(guild_id)
    return g.name if g else f"Left server ({guild_id})"

  @staticmethod
  def _top(rows, fmt) -> str:
    return "\n".join(fmt(*r) for r in rows) or "—"

  def _base_embed(self, title: str, period: str) -> discord.Embed:
    e = discord.Embed(title=title, color=COLOR, timestamp=discord.utils.utcnow())
    e.set_footer(text=f"Period: {PERIOD_LABEL[period]}")
    return e

  async def _summary(self, where: str, params: tuple):
    totals = await self._run(
        self._query,
        f"SELECT COUNT(*), COUNT(DISTINCT user_id), COUNT(DISTINCT guild_id), COALESCE(SUM(slash), 0) FROM uses WHERE {where}",
        params,
    )
    return totals[0]

  # ---- commands

  async def cog_check(self, ctx: commands.Context) -> bool:
    # Owner only, for prefix and slash (slash subcommands don't run the group's own checks).
    return await self.bot.is_owner(ctx.author)

  @commands.hybrid_group(name="usage", invoke_without_command=True, fallback="overview")
  @app_commands.describe(period="How far back to look (default: week)")
  async def usage(self, ctx: commands.Context, period: Period = "week"):
    """Overall bot usage: commands run, people, servers, top commands and cogs.

    Periods: day, week, month, year, all.
    """
    await ctx.defer(ephemeral=True)
    await self._flush()
    since = _since(period)
    total, users, guilds, slash = await self._summary("ts >= ?", (since,))
    e = self._base_embed("📊 Bot usage", period)
    if not total:
      e.description = "No commands have been used in this period yet."
      await ctx.send(embed=e, ephemeral=True)
      return
    e.add_field(name="Commands run", value=f"**{total:,}**\n/ slash: {slash:,}\nprefix: {total - slash:,}", inline=True)
    e.add_field(name="People", value=f"**{users:,}** unique users", inline=True)
    e.add_field(name="Servers", value=f"**{guilds:,}** servers used it\nbot is in {len(self.bot.guilds):,}", inline=True)

    top_cmds = await self._run(
        self._query, "SELECT command, COUNT(*) c FROM uses WHERE ts >= ? GROUP BY command ORDER BY c DESC LIMIT 10", (since,)
    )
    top_cogs = await self._run(
        self._query,
        "SELECT COALESCE(cog, 'No cog'), COUNT(*) c, COUNT(DISTINCT user_id) FROM uses WHERE ts >= ? GROUP BY cog ORDER BY c DESC LIMIT 8",
        (since,),
    )
    top_guilds = await self._run(
        self._query, "SELECT guild_id, COUNT(*) c FROM uses WHERE ts >= ? GROUP BY guild_id ORDER BY c DESC LIMIT 5", (since,)
    )
    e.add_field(name="Top commands", value=self._top(top_cmds, lambda n, c: f"`{n}` — {c:,}"), inline=True)
    e.add_field(name="Top cogs", value=self._top(top_cogs, lambda n, c, u: f"**{n}** — {c:,} ({u:,} people)"), inline=True)
    e.add_field(
        name="Busiest servers",
        value=self._top(top_guilds, lambda g, c: f"{discord.utils.escape_markdown(self._guild_name(g))[:40]} — {c:,}"),
        inline=False,
    )
    await ctx.send(embed=e, ephemeral=True)

  @usage.command(name="command")
  @app_commands.describe(name="Command name, e.g. nationalrail departures", period="How far back to look (default: week)")
  async def usage_command(self, ctx: commands.Context, name: str, period: Period = "week"):
    """Usage of one command (subcommands included)."""
    await self._detail(ctx, "command", name.strip().lower(), period)

  @usage.command(name="cog")
  @app_commands.describe(name="Cog name, e.g. NationalRail", period="How far back to look (default: week)")
  async def usage_cog(self, ctx: commands.Context, name: str, period: Period = "week"):
    """Usage of every command in one cog."""
    await self._detail(ctx, "cog", name.strip(), period)

  async def _detail(self, ctx: commands.Context, kind: str, name: str, period: str):
    await ctx.defer(ephemeral=True)
    await self._flush()
    since = _since(period)
    if kind == "command":
      where, params = "ts >= ? AND (command = ? OR command LIKE ?)", (since, name, name + " %")
    else:
      where, params = "ts >= ? AND LOWER(cog) = LOWER(?)", (since, name)
    total, users, guilds, slash = await self._summary(where, params)
    e = self._base_embed(f"📊 Usage of {kind} `{name}`", period)
    if not total:
      e.description = f"No uses of that {kind} in this period."
      await ctx.send(embed=e, ephemeral=True)
      return
    e.add_field(name="Uses", value=f"**{total:,}**\n/ slash: {slash:,}\nprefix: {total - slash:,}", inline=True)
    e.add_field(name="People", value=f"**{users:,}**", inline=True)
    e.add_field(name="Servers", value=f"**{guilds:,}**", inline=True)
    subs = await self._run(
        self._query, f"SELECT command, COUNT(*) c FROM uses WHERE {where} GROUP BY command ORDER BY c DESC LIMIT 10", params
    )
    if len(subs) > 1 or kind == "cog":
      e.add_field(name="By command", value=self._top(subs, lambda n, c: f"`{n}` — {c:,}"), inline=False)
    await ctx.send(embed=e, ephemeral=True)

  @usage.command(name="reset")
  async def usage_reset(self, ctx: commands.Context, confirm: bool = False):
    """Delete all recorded usage. Run with `True` to confirm."""
    if not confirm:
      await ctx.send(
          embed=discord.Embed(description="This deletes **all** usage history. Run it again with `True` to confirm.", color=discord.Color.orange()),
          ephemeral=True,
      )
      return
    async with self._lock:
      self._buffer.clear()
    await self._run(self._query, "DELETE FROM uses")
    await ctx.send(embed=discord.Embed(description="🧹 Usage history deleted.", color=discord.Color.green()), ephemeral=True)

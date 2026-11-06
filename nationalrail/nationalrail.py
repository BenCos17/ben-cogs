"""National Rail Enquiries live departure boards (Darwin LDBWS via the Rail Data Marketplace).

Ported from the UK Transport Boards dev portal (lib/depboard-ldbws.js):

    GET {base}/api/20220120/GetDepBoardWithDetails/{CRS}?numRows=&timeWindow=&filterCrs=&filterType=to
    base = https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS
    Auth header: x-apikey

One call returns the whole board including calling points, so there are no per-train follow-up calls.
"""

import asyncio
import html
import json
import re
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import discord
from redbot.core import Config, app_commands, commands
from redbot.core.data_manager import bundled_data_path

API_VERSION = "20220120"
DEFAULT_LDBWS_URL = "https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS"
TOKEN_SERVICE = "nationalrail"
CACHE_TTL = 60  # seconds per station + filter, same as the portal
ERROR_TTL = 15
MAX_PER_MINUTE = 30
NUM_ROWS = 10
TIME_WINDOW_MINS = 120
NRE_RED = discord.Color.from_rgb(0xE2, 0x1E, 0x26)
CRS_RE = re.compile(r"^[A-Za-z]{3}$")


class NationalRailError(Exception):
  pass


def _clock(value) -> str:
  s = str(value or "").strip()
  return s if re.match(r"^\d{2}:\d{2}$", s) else ""


def _places(locations) -> str:
  names = []
  for loc in locations or []:
    name = str((loc or {}).get("locationName") or "").strip()
    if name and name not in names:
      names.append(name)
  return " & ".join(names)


def _strip_html(text: str) -> str:
  text = re.sub(r"<br\s*/?>", "\n", str(text or ""), flags=re.I)
  text = re.sub(r"<[^>]+>", "", text)
  return re.sub(r"[ \t]+", " ", html.unescape(text)).strip()


def _reason(raw: str) -> str:
  return re.sub(
      r"^This (?:train|service) (?:has been|is) (?:cancelled|delayed)\s*(?:because of|due to|by)?\s*",
      "",
      str(raw or ""),
      flags=re.I,
  ).rstrip(". ").strip()


def _fit(text: str, width: int) -> str:
  text = str(text or "")
  return text if len(text) <= width else text[: width - 1] + "…"


def _embed(title: str, description: str = "", color: discord.Color = NRE_RED) -> discord.Embed:
  e = discord.Embed(title=_fit(title, 256), description=_fit(description, 4096), color=color)
  e.set_footer(text="Powered by National Rail Enquiries")
  return e


def _error(description: str) -> discord.Embed:
  return _embed("❌ Something went wrong", description, discord.Color.dark_red())


def _services(board: dict) -> List[dict]:
  out = []
  for key in ("trainServices", "busServices", "ferryServices"):
    out.extend(board.get(key) or [])
  # Keep the order the board gives, but make sure everything has a departure time.
  return [s for s in out if _clock(s.get("std"))]


class ServiceSelect(discord.ui.Select):
  def __init__(self, board_view: "BoardView"):
    self.board_view = board_view
    options = []
    for i, svc in enumerate(board_view.services[:25]):
      dest = _places(svc.get("currentDestinations") or svc.get("destination")) or "Unknown"
      etd = str(svc.get("etd") or "")
      label = _fit(f"{svc.get('std')} {dest}", 100)
      desc = _fit(f"{etd} · Plat {svc.get('platform') or '-'} · {svc.get('operator') or ''}", 100)
      options.append(discord.SelectOption(label=label, value=str(i), description=desc))
    super().__init__(placeholder="Show calling points for a service…", options=options, min_values=1, max_values=1)

  async def callback(self, interaction: discord.Interaction):
    svc = self.board_view.services[int(self.values[0])]
    embed = self.board_view.cog.service_embed(self.board_view.board, svc)
    await interaction.response.send_message(embed=embed, ephemeral=True)


class BoardView(discord.ui.View):
  def __init__(self, cog: "NationalRail", author_id: int, crs: str, filter_crs: Optional[str], board: dict):
    super().__init__(timeout=300)
    self.cog = cog
    self.author_id = author_id
    self.crs = crs
    self.filter_crs = filter_crs
    self.message: Optional[discord.Message] = None
    self._load(board)

  def _load(self, board: dict):
    self.board = board
    self.services = _services(board)[:NUM_ROWS]
    for item in list(self.children):
      if isinstance(item, ServiceSelect):
        self.remove_item(item)
    if self.services:
      self.add_item(ServiceSelect(self))

  @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
  async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
    if interaction.user.id != self.author_id:
      await interaction.response.send_message(embed=_error("Only the person who asked for this board can refresh it."), ephemeral=True)
      return
    await interaction.response.defer()
    try:
      board = await self.cog.fetch_board(self.crs, self.filter_crs)
    except NationalRailError as e:
      await interaction.followup.send(embed=_error(str(e)), ephemeral=True)
      return
    self._load(board)
    await interaction.edit_original_response(embed=self.cog.board_embed(board, self.filter_crs), view=self)

  async def on_timeout(self):
    for item in self.children:
      item.disabled = True
    if self.message:
      try:
        await self.message.edit(view=self)
      except discord.HTTPException:
        pass


class StationPicker(discord.ui.View):
  """Dropdown shown when a station name matches more than one station."""

  def __init__(self, author_id: int, matches: List[dict]):
    super().__init__(timeout=60)
    self.author_id = author_id
    self.choice: Optional[str] = None
    self.message: Optional[discord.Message] = None
    select = discord.ui.Select(
        placeholder="Choose the station…",
        options=[discord.SelectOption(label=_fit(m["name"], 100), value=m["crs"], description=m["crs"]) for m in matches[:25]],
    )
    select.callback = self._picked
    self.select = select
    self.add_item(select)

  async def _picked(self, interaction: discord.Interaction):
    if interaction.user.id != self.author_id:
      await interaction.response.send_message(embed=_error("This menu isn't for you."), ephemeral=True)
      return
    self.choice = self.select.values[0]
    await interaction.response.edit_message(embed=_embed("✅ Station selected", f"Loading **{self.choice}**…"), view=None)
    self.stop()

  async def on_timeout(self):
    if self.message:
      try:
        await self.message.edit(embed=_embed("⌛ Timed out", "No station was picked.", discord.Color.greyple()), view=None)
      except discord.HTTPException:
        pass


class NationalRail(commands.Cog):
  """National Rail Enquiries live departure boards for Great Britain."""

  def __init__(self, bot):
    self.bot = bot
    self.config = Config.get_conf(self, identifier=492089091320446977, force_registration=True)
    self.config.register_global(user_agent="Red-DiscordBot (NationalRail Cog)")
    self.session: Optional[aiohttp.ClientSession] = None
    self._cache: Dict[Tuple[str, str], Tuple[float, object]] = {}
    self._inflight: Dict[Tuple[str, str], asyncio.Task] = {}
    self._recent_calls: List[float] = []
    self.stations: List[dict] = []
    self._by_crs: Dict[str, dict] = {}

  async def cog_load(self):
    self.session = aiohttp.ClientSession()
    path = bundled_data_path(self) / "uk-stations.json"
    with open(path, encoding="utf-8") as f:
      self.stations = sorted(json.load(f), key=lambda s: s["name"])
    self._by_crs = {s["crs"].upper(): s for s in self.stations}

  async def cog_unload(self):
    for task in self._inflight.values():
      task.cancel()
    if self.session:
      await self.session.close()

  async def red_delete_data_for_user(self, **kwargs):
    return  # nothing stored per user

  # ---- API

  async def _api_settings(self) -> Tuple[str, str]:
    tokens = await self.bot.get_shared_api_tokens(TOKEN_SERVICE)
    key = (tokens.get("ldbws_key") or "").strip()
    base = (tokens.get("ldbws_url") or DEFAULT_LDBWS_URL).strip()
    # Accept the product root (…/LDBWS) or a full operation URL pasted from the docs.
    base = re.sub(r"/api/.*$", "", base, flags=re.I).rstrip("/")
    return key, base

  def _under_cap(self) -> bool:
    cutoff = time.monotonic() - 60
    self._recent_calls = [t for t in self._recent_calls if t >= cutoff]
    return len(self._recent_calls) < MAX_PER_MINUTE

  async def _fetch_uncached(self, crs: str, filter_crs: Optional[str]) -> dict:
    key, base = await self._api_settings()
    if not key or not base.lower().startswith("https://"):
      raise NationalRailError(
          "National Rail isn't set up yet. The bot owner needs to run "
          f"`[p]set api {TOKEN_SERVICE} ldbws_key,<key>` (see `[p]nrset`)."
      )
    if not self._under_cap():
      raise NationalRailError(f"National Rail: {MAX_PER_MINUTE} calls a minute reached, try again shortly.")
    self._recent_calls.append(time.monotonic())

    params = {"numRows": str(NUM_ROWS), "timeWindow": str(TIME_WINDOW_MINS)}
    if filter_crs:
      params["filterCrs"] = filter_crs
      params["filterType"] = "to"
    url = f"{base}/api/{API_VERSION}/GetDepBoardWithDetails/{crs}"
    headers = {"x-apikey": key, "Accept": "application/json", "User-Agent": await self.config.user_agent()}
    try:
      async with self.session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        text = await resp.text()
        status = resp.status
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
      raise NationalRailError(f"National Rail is unreachable right now ({type(e).__name__}).")
    if status == 429:
      raise NationalRailError("National Rail rate limit reached, try again in a minute.")
    if status in (401, 403):
      raise NationalRailError(f"National Rail refused the API key (HTTP {status}). Check the LDBWS key.")
    if status in (400, 404, 500) and "invalid crs" in text.lower():
      raise NationalRailError(f"National Rail doesn't know the station **{crs}**.")
    if status >= 400:
      raise NationalRailError(f"National Rail returned HTTP {status}.")
    try:
      return json.loads(text)
    except ValueError:
      raise NationalRailError("National Rail sent a reply that isn't JSON.")

  async def fetch_board(self, crs: str, filter_crs: Optional[str] = None) -> dict:
    """One departure board, cached for a minute per station + "calling at" filter."""
    cache_key = (crs, filter_crs or "")
    hit = self._cache.get(cache_key)
    if hit and hit[0] > time.monotonic():
      if isinstance(hit[1], NationalRailError):
        raise hit[1]
      return hit[1]
    task = self._inflight.get(cache_key)
    if task is None:
      task = asyncio.ensure_future(self._fetch_uncached(crs, filter_crs))
      self._inflight[cache_key] = task
      try:
        result = await asyncio.shield(task)
        self._cache[cache_key] = (time.monotonic() + CACHE_TTL, result)
      except NationalRailError as e:
        self._cache[cache_key] = (time.monotonic() + ERROR_TTL, e)
        raise
      finally:
        self._inflight.pop(cache_key, None)
      if len(self._cache) > 300:
        now = time.monotonic()
        self._cache = {k: v for k, v in self._cache.items() if v[0] > now}
      return result
    return await asyncio.shield(task)

  # ---- stations

  def search_stations(self, query: str) -> List[dict]:
    q = query.strip().lower()
    if not q:
      return []
    exact = [s for s in self.stations if s["name"].lower() == q or s["crs"].lower() == q]
    if exact:
      return exact
    starts = [s for s in self.stations if s["name"].lower().startswith(q)]
    contains = [s for s in self.stations if q in s["name"].lower() and s not in starts]
    return starts + contains

  async def resolve_station(self, ctx: commands.Context, query: str) -> Optional[str]:
    query = query.strip()
    if CRS_RE.match(query) and query.upper() in self._by_crs:
      return query.upper()
    matches = self.search_stations(query)
    if not matches:
      if CRS_RE.match(query):
        return query.upper()  # unknown to our list; let National Rail decide
      await ctx.send(embed=_error(f"No station found matching **{query}**.\nTry `/nationalrail search` to look it up."))
      return None
    if len(matches) == 1:
      return matches[0]["crs"]
    embed = _embed(f"🔎 Several stations match '{_fit(query, 60)}'", "Pick the one you meant from the menu below.", discord.Color.orange())
    view = StationPicker(ctx.author.id, matches)
    view.message = await ctx.send(embed=embed, view=view)
    await view.wait()
    return view.choice

  def station_name(self, crs: str) -> str:
    s = self._by_crs.get(crs.upper())
    return s["name"] if s else crs.upper()

  # ---- embeds

  def board_embed(self, board: dict, filter_crs: Optional[str]) -> discord.Embed:
    name = board.get("locationName") or board.get("crs") or "?"
    crs = board.get("crs") or ""
    title = f"🚉 {name} ({crs}) — Departures"
    if filter_crs:
      title += f" calling at {board.get('filterLocationName') or self.station_name(filter_crs)}"
    services = _services(board)[:NUM_ROWS]

    if services:
      rows = [f"{'Time':<5} {'Destination':<22} {'Plat':<4} Expected"]
      for svc in services:
        dest = _places(svc.get("currentDestinations") or svc.get("destination")) or "?"
        kind = str(svc.get("serviceType") or "train").lower()
        if kind == "bus":
          dest = "🚌" + dest
        elif kind == "ferry":
          dest = "⛴" + dest
        plat = str(svc.get("platform") or ("BUS" if kind == "bus" else "-"))
        etd = "Cancelled" if svc.get("isCancelled") else str(svc.get("etd") or "")
        rows.append(f"{svc.get('std'):<5} {_fit(dest, 22):<22} {_fit(plat, 4):<4} {etd}")
      desc = "```\n" + "\n".join(rows) + "\n```"
    else:
      desc = "No departures in the next two hours."
      if board.get("areServicesAvailable") is False:
        desc = "Live departures aren't available for this station right now."

    embed = discord.Embed(title=_fit(title, 256), description=desc, color=NRE_RED, timestamp=discord.utils.utcnow())
    embed.set_author(name="Live departures · National Rail")

    problems = []
    for svc in services:
      dest = _places(svc.get("currentDestinations") or svc.get("destination"))
      if svc.get("isCancelled") and svc.get("cancelReason"):
        problems.append(f"**{svc.get('std')} to {dest}** cancelled: {_reason(svc['cancelReason'])}")
      elif svc.get("delayReason"):
        problems.append(f"**{svc.get('std')} to {dest}** delayed: {_reason(svc['delayReason'])}")
    if problems:
      embed.add_field(name="Delays & cancellations", value=_fit("\n".join(problems[:5]), 1024), inline=False)

    messages = [_strip_html(m.get("Value") or m.get("value") or "") for m in board.get("nrccMessages") or []]
    messages = [m for m in messages if len(m) >= 3]
    if messages:
      embed.add_field(name="⚠️ Station messages", value=_fit("\n\n".join(messages[:3]), 1024), inline=False)

    generated = str(board.get("generatedAt") or "")
    stamp = generated[11:16] if len(generated) >= 16 else ""
    embed.set_footer(text="Powered by National Rail Enquiries" + (f" · updated {stamp}" if stamp else ""))
    return embed

  def service_embed(self, board: dict, svc: dict) -> discord.Embed:
    dest = _places(svc.get("currentDestinations") or svc.get("destination")) or "?"
    origin = _places(svc.get("currentOrigins") or svc.get("origin")) or "?"
    cancelled = bool(svc.get("isCancelled"))
    etd = "Cancelled" if cancelled else str(svc.get("etd") or "")
    embed = discord.Embed(
        title=_fit(f"{svc.get('std')} {board.get('locationName', '')} → {dest}", 256),
        color=discord.Color.dark_grey() if cancelled else NRE_RED,
    )
    embed.add_field(name="Expected", value=etd or "-", inline=True)
    embed.add_field(name="Platform", value=str(svc.get("platform") or "-"), inline=True)
    embed.add_field(name="Operator", value=str(svc.get("operator") or "-"), inline=True)
    coaches = svc.get("length") or len(((svc.get("formation") or {}).get("coaches")) or [])
    if coaches:
      embed.add_field(name="Coaches", value=str(coaches), inline=True)
    embed.add_field(name="From", value=origin, inline=True)
    reason = svc.get("cancelReason") if cancelled else svc.get("delayReason")
    if reason:
      embed.add_field(name="Reason", value=_fit(_reason(reason), 1024), inline=False)

    lists = svc.get("subsequentCallingPoints") or []
    points = (lists[0].get("callingPoint") if lists else None) or []
    lines = []
    for cp in points:
      name = cp.get("locationName") or "?"
      st = _clock(cp.get("st")) or "--:--"
      et = str(cp.get("et") or cp.get("at") or "")
      if cp.get("isCancelled"):
        et = "Cancelled"
      lines.append(f"{st}  {_fit(name, 26):<26} {et}")
    if lines:
      text = "```\n" + "\n".join(lines) + "\n```"
      if len(text) > 1024:
        keep = []
        for line in lines:
          if len("\n".join(keep + [line])) > 990:
            keep.append("…")
            break
          keep.append(line)
        text = "```\n" + "\n".join(keep) + "\n```"
      embed.add_field(name="Calling at", value=text, inline=False)
    embed.set_footer(text="Powered by National Rail Enquiries")
    return embed

  # ---- autocomplete

  async def _station_autocomplete(self, interaction: discord.Interaction, current: str):
    matches = self.search_stations(current) if current else self.stations
    return [app_commands.Choice(name=_fit(f"{s['name']} ({s['crs']})", 100), value=s["crs"]) for s in matches[:25]]

  # ---- commands

  @commands.hybrid_group(name="nationalrail", aliases=["nr", "ukrail"])
  async def nationalrail(self, ctx: commands.Context):
    """National Rail (Great Britain) live departure boards."""
    if ctx.invoked_subcommand is None:
      await ctx.send_help()

  async def _send_board(self, ctx: commands.Context, station: str, calling_at: Optional[str]):
    crs = await self.resolve_station(ctx, station)
    if not crs:
      return
    filter_crs = None
    if calling_at:
      filter_crs = await self.resolve_station(ctx, calling_at)
      if not filter_crs:
        return
    async with ctx.typing():
      try:
        board = await self.fetch_board(crs, filter_crs)
      except NationalRailError as e:
        await ctx.send(embed=_error(str(e).replace("[p]", ctx.clean_prefix)))
        return
    view = BoardView(self, ctx.author.id, crs, filter_crs, board)
    view.message = await ctx.send(embed=self.board_embed(board, filter_crs), view=view)

  @nationalrail.command(name="departures", aliases=["board", "dep", "deps"])
  @app_commands.describe(
      station="Station name or 3-letter code, e.g. Cardiff Central or CDF",
      calling_at="Only show trains calling at this station (optional)",
  )
  @app_commands.autocomplete(station=_station_autocomplete, calling_at=_station_autocomplete)
  async def nr_departures(self, ctx: commands.Context, station: str, *, calling_at: Optional[str] = None):
    """Show the live departure board for a station.

    Use quotes or the 3-letter code for station names with spaces in prefix commands.

    Examples:
    - `[p]nr departures PAD`
    - `[p]nr departures "Cardiff Central" Bristol Temple Meads`
    """
    await self._send_board(ctx, station, calling_at)

  @nationalrail.command(name="search", aliases=["lookup", "crs"])
  @app_commands.describe(query="Part of a station name or a 3-letter code")
  async def nr_search(self, ctx: commands.Context, *, query: str):
    """Find a station's 3-letter code (CRS)."""
    matches = self.search_stations(query)
    if not matches:
      await ctx.send(embed=_error(f"No stations found matching **{query}**."))
      return
    lines = [f"`{s['crs']}` {s['name']}" for s in matches[:20]]
    if len(matches) > 20:
      lines.append(f"…and {len(matches) - 20} more")
    embed = _embed(f"🔍 Stations matching '{query}'", "\n".join(lines))
    embed.set_footer(text=f"{len(matches)} match(es) · use the code with /nationalrail departures")
    await ctx.send(embed=embed)

  # ---- owner settings

  @commands.hybrid_group(name="nrset", invoke_without_command=True, fallback="status")
  @commands.is_owner()
  async def nrset(self, ctx: commands.Context):
    """Set up the National Rail cog and show its status."""
    key, base = await self._api_settings()
    p = ctx.clean_prefix
    embed = _embed("⚙️ National Rail setup", "Live departures come from the Rail Data Marketplace **Live Departure Board** product (Darwin LDBWS).")
    embed.add_field(
        name="Steps",
        value=(
            "1. Sign up at <https://raildata.org.uk> and subscribe to **Live Departure Board**.\n"
            f"2. `{p}set api {TOKEN_SERVICE} ldbws_key,<consumer key>`\n"
            f"3. Optional: `{p}set api {TOKEN_SERVICE} ldbws_url,<product URL>`"
        ),
        inline=False,
    )
    embed.add_field(name="Key set", value="✅ Yes" if key else "❌ No", inline=True)
    embed.add_field(name="Cached boards", value=str(len(self._cache)), inline=True)
    embed.add_field(name="URL", value=f"`{base}`", inline=False)
    await ctx.send(embed=embed, ephemeral=True)

  @nrset.command(name="useragent")
  @app_commands.describe(user_agent="New User-Agent (leave empty to see the current one)")
  async def nrset_useragent(self, ctx: commands.Context, *, user_agent: Optional[str] = None):
    """View or set the User-Agent sent to National Rail."""
    if not user_agent:
      await ctx.send(embed=_embed("🔍 User-Agent", f"`{await self.config.user_agent()}`"), ephemeral=True)
      return
    await self.config.user_agent.set(user_agent)
    await ctx.send(embed=_embed("✅ User-Agent updated", f"`{user_agent}`", discord.Color.green()), ephemeral=True)

  @nrset.command(name="clearcache")
  async def nrset_clearcache(self, ctx: commands.Context):
    """Clear cached departure boards."""
    n = len(self._cache)
    self._cache.clear()
    await ctx.send(embed=_embed("🧹 Cache cleared", f"Removed {n} cached board(s).", discord.Color.green()), ephemeral=True)

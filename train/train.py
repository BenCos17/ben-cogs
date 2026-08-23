import aiohttp
import discord
from redbot.core import app_commands, commands


class Train(commands.Cog):
  """Interact with the Iarnród Éireann (Irish Rail) REST API v1."""

  def __init__(self, bot):
    self.bot = bot
    self.base_url = "https://ie.api.thediabetic.dev"

  async def _make_request(self, endpoint: str, params: dict = None):
    """Helper method to fetch data from the Irish Rail REST API safely."""
    url = f"{self.base_url}{endpoint}"
    try:
      async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=10) as response:
          data = await response.json()
          return response.status, data
    except Exception as e:
      print(f"[Train API Error] Could not connect to {url}: {e}")
      return 500, None

  # --- Train Commands ---

  @commands.hybrid_group(name="train", aliases=["trains"])
  async def train(self, ctx: commands.Context):
    """Irish Rail train commands."""
    if ctx.invoked_subcommand is None:
      await ctx.send_help()

  @train.command(name="all")
  @app_commands.describe(train_type="Filter trains by type (A, D, S, M)")
  async def train_all(self, ctx: commands.Context, train_type: str = None):
    """Get all running trains, optionally filtered by type."""
    async with ctx.typing():
      params = {"type": train_type.upper()} if train_type else None
      status, data = await self._make_request("/trains", params=params)

      if status != 200 or not data or not data.get("success"):
        await ctx.send(
            "❌ Could not fetch train data or the API is currently unavailable."
        )
        return

      trains = data.get("trains", [])
      embed = discord.Embed(
          title="🚆 Live Irish Rail Trains",
          description=f"Currently tracking **{len(trains)}** active trains across the network.",
          color=discord.Color.green(),
      )

      sample = trains[:5]
      sample_text = ""
      for t in sample:
        sample_text += (
            f"• **{t.get('code')}**: {t.get('public_message', 'No info')}"
            f" (Status: {t.get('status')})\n"
        )

      if sample_text:
        embed.add_field(
            name="Sample of Running Trains", value=sample_text, inline=False
        )
      embed.set_footer(text="Data source: Iarnród Éireann REST API v1")
      await ctx.send(embed=embed)

  @train.command(name="info")
  @app_commands.describe(code="The train's 4-character code (e.g., E401)")
  async def train_info(self, ctx: commands.Context, code: str):
    """Get details for a specific train by its code."""
    async with ctx.typing():
      status, data = await self._make_request(f"/trains/{code.upper()}")

      if status == 404 or (data and not data.get("success")):
        err_msg = (
            data.get("errorMessage", f"Train code {code.upper()} not found.")
            if data
            else f"Train code {code.upper()} not found."
        )
        await ctx.send(f"❌ {err_msg}")
        return

      if status != 200 or not data or "train" not in data:
        await ctx.send(f"❌ Could not retrieve details for train {code.upper()}.")
        return

      t = data["train"]
      embed = discord.Embed(
          title=f"🚆 Train Details: {t.get('code', code.upper())}",
          description=f"**Message:** {t.get('public_message', 'N/A')}",
          color=discord.Color.blue(),
      )
      embed.add_field(name="Direction", value=t.get("direction", "N/A"), inline=True)
      embed.add_field(name="Status", value=t.get("status", "N/A"), inline=True)
      embed.add_field(name="Date", value=t.get("date", "N/A"), inline=True)

      await ctx.send(embed=embed)

  # --- Station Commands ---

  @commands.hybrid_group(name="station", aliases=["stations"])
  async def station(self, ctx: commands.Context):
    """Irish Rail station commands."""
    if ctx.invoked_subcommand is None:
      await ctx.send_help()

  @station.command(name="timetable")
  @app_commands.describe(code="The 5-character station code (e.g., CNLLY)")
  async def station_timetable(self, ctx: commands.Context, code: str):
    """Get the live timetable for a specific station code."""
    async with ctx.typing():
      status, data = await self._make_request(f"/stations/{code.upper()}/timetable")

      if status == 404 or (data and not data.get("success")):
        err_msg = (
            data.get("errorMessage", f"No station found matching code '{code.upper()}'")
            if data
            else f"No station found matching code '{code.upper()}'"
        )
        await ctx.send(f"❌ {err_msg}")
        return

      if status != 200 or not data or "timetable" not in data:
        await ctx.send(f"❌ Could not retrieve timetable for station **{code.upper()}**.")
        return

      timetable = data["timetable"]
      embed = discord.Embed(
          title=f"🕒 Timetable for Station: {code.upper()}",
          description=f"Found **{len(timetable)}** upcoming movements.",
          color=discord.Color.orange(),
      )

      timetable_snippet = ""
      for t in timetable[:8]:
        timetable_snippet += (
            f"• **{t.get('train_type')}** ({t.get('train_code')}) to **{t.get('destination')}** — "
            f"Due in **{t.get('due_in')}m** (Exp: {t.get('exp_arrival')})\n"
        )

      if timetable_snippet:
        embed.add_field(name="Upcoming Services", value=timetable_snippet, inline=False)
      else:
        embed.add_field(name="Upcoming Services", value="No upcoming services listed right now.", inline=False)

      await ctx.send(embed=embed)



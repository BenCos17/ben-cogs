import aiohttp
import discord
from redbot.core import app_commands, commands


class Train(commands.Cog):
  """Interact with the Iarnród Éireann (Irish Rail) REST API v1."""

  def __init__(self, bot):
    self.bot = bot
    self.base_url = "https://api.irishrail.ie/rest"  # Base or custom REST wrapper URL

  async def _make_request(self, endpoint: str, params: dict = None):
    """Helper method to fetch data from the Irish Rail REST API."""
    url = f"{self.base_url}{endpoint}"
    async with aiohttp.ClientSession() as session:
      async with session.get(url, params=params) as response:
        if response.status != 200:
          return None
        return await response.json()

  # --- Train Commands ---

  @commands.hybrid_group(name="train", aliases=["trains"])
  async def train(self, ctx: commands.Context):
    """Irish Rail train commands."""
    if ctx.invoked_subcommand is None:
      await ctx.send_help()

  @train.command(name="all")
  async def train_all(self, ctx: commands.Context):
    """Get a count and sample of all currently running trains."""
    async with ctx.typing():
      data = await self._make_request("/trains")
      if not data or "objTrainPositions" not in data:
        await ctx.send(
            "❌ Could not fetch train data or the API is currently unavailable."
        )
        return

      trains = data["objTrainPositions"]
      embed = discord.Embed(
          title="🚆 Live Irish Rail Trains",
          description=f"Currently tracking **{len(trains)}** active trains across the network.",
          color=discord.Color.green(),
      )

      # Display a small sample to avoid spamming the chat
      sample = trains[:5]
      sample_text = ""
      for t in sample:
        sample_text += (
            f"• **{t.get('TrainCode')}**: {t.get('PublicMessage', 'No info')}"
            f" (Status: {t.get('TrainStatus')})\n"
        )

      if sample_text:
        embed.add_field(
            name="Sample of Running Trains", value=sample_text, inline=False
        )
      embed.set_footer(text="Data source: Iarnród Éireann REST API v1")
      await ctx.send(embed=embed)

  @train.command(name="info")
  @app_commands.describe(code="The unique train code (e.g., E810)")
  async def train_info(self, ctx: commands.Context, code: str):
    """Get details for a specific train by its code."""
    async with ctx.typing():
      data = await self._make_request(f"/trains/{code.upper()}")
      if not data or not data.get("objTrainMovements"):
        await ctx.send(
            f"❌ Train code **{code.upper()}** not found or not currently"
            " running."
        )
        return

      embed = discord.Embed(
          title=f"🚆 Train Details: {code.upper()}",
          color=discord.Color.blue(),
      )

      movements = data["objTrainMovements"]
      if movements:
        first = movements[0]
        embed.add_field(
            name="Journey Info",
            value=(
                f"• **Origin:** {first.get('LocationFullName')}\n• **Server"
                f" Time:** {first.get('ServerTime')}"
            ),
            inline=False,
        )

      # Show up to 5 recent/upcoming movements
      mov_text = ""
      for m in movements[:5]:
        mov_text += (
            f"• **{m.get('LocationFullName')}** — Arr: {m.get('Arr', 'N/E')} |"
            f" Dep: {m.get('Dep', 'N/E')}\n"
        )

      if mov_text:
        embed.add_field(
            name="Recent/Next Stops", value=mov_text, inline=False
        )

      await ctx.send(embed=embed)

  # --- Station Commands ---

  @commands.hybrid_group(name="station", aliases=["stations"])
  async def station(self, ctx: commands.Context):
    """Irish Rail station commands."""
    if ctx.invoked_subcommand is None:
      await ctx.send_help()

  @station.command(name="search")
  @app_commands.describe(code="The station code (e.g., HUSTN, CONN, CORK)")
  async def station_timetable(self, ctx: commands.Context, code: str):
    """Get the live timetable for a specific station code."""
    async with ctx.typing():
      # Fetching station timetable endpoint
      data = await self._make_request(f"/stations/{code.upper()}/timetable")
      if not data or "objStationData" not in data:
        await ctx.send(
            f"❌ Could not retrieve timetable for station code **{code.upper()}**."
            " Check the code."
        )
        return

      trains = data["objStationData"]
      embed = discord.Embed(
          title=f"🕒 Timetable for Station: {code.upper()}",
          description=f"Found **{len(trains)}** upcoming movements.",
          color=discord.Color.orange(),
      )

      timetable_snippet = ""
      for t in trains[:8]:  # Limit to 8 entries to fit nicely in an embed
        timetable_snippet += (
            f"• **{t.get('Traintype')}** to **{t.get('Destination')}** — Due:"
            f" **{t.get('Duein')}m** (Exp: {t.get('Expectedarrival')})\n"
        )

      if timetable_snippet:
        embed.add_field(
            name="Upcoming Services", value=timetable_snippet, inline=False
        )
      else:
        embed.add_field(
            name="Upcoming Services",
            value="No upcoming services listed right now.",
            inline=False,
        )

      await ctx.send(embed=embed)



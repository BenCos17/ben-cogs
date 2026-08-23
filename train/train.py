import aiohttp
import discord
from redbot.core import Config, app_commands, commands


class Train(commands.Cog):
  """Interact with the Iarnród Éireann (Irish Rail) REST API v1."""

  def __init__(self, bot):
    self.bot = bot
    self.base_url = "https://ie.api.thediabetic.dev"
    
    # Initialize Red's Config for settings (using your specified identifier)
    self.config = Config.get_conf(
        self, identifier=492089091320446976, force_registration=True
    )
    default_global = {"user_agent": "Red-DiscordBot (IrishRail Cog)"}
    self.config.register_global(**default_global)

  async def _get_headers(self) -> dict:
    """Retrieves the configured User-Agent and formats request headers."""
    ua = await self.config.user_agent()
    return {
        "User-Agent": ua,
        "Accept": "application/json"
    }

  async def _make_request(self, endpoint: str, params: dict = None):
    """Helper method to fetch data from the Irish Rail REST API safely."""
    url = f"{self.base_url}{endpoint}"
    headers = await self._get_headers()
    try:
      async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers, timeout=10) as response:
          data = await response.json()
          return response.status, data
    except Exception as e:
      print(f"[Train API Error] Could not connect to {url}: {e}")
      return 500, None

  # --- Settings / Config Group (Owner Only) ---

  @commands.group(name="trainset", invoke_without_command=True)
  @commands.is_owner()
  async def trainset(self, ctx: commands.Context):
    """Configure settings for the Train cog."""
    await ctx.send_help()

  @trainset.command(name="useragent")
  @commands.is_owner()
  async def trainset_useragent(self, ctx: commands.Context, *, user_agent: str = None):
    """View or set the custom User-Agent used for API requests."""
    if not user_agent:
      current_ua = await self.config.user_agent()
      await ctx.send(f"🔍 Current API `User-Agent` is configured as:\n`{current_ua}`")
      return

    await self.config.user_agent.set(user_agent)
    await ctx.send(f"✅ Successfully updated custom `User-Agent` to:\n`{user_agent}`")

  @trainset.command(name="resetuseragent")
  @commands.is_owner()
  async def trainset_resetuseragent(self, ctx: commands.Context):
    """Reset the User-Agent back to the default value."""
    await self.config.user_agent.clear()
    default_ua = await self.config.user_agent()
    await ctx.send(f"🔄 Reset `User-Agent` back to default:\n`{default_ua}`")

  # --- Train Commands Group ---

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
        await ctx.send("❌ Could not fetch train data or the API is currently unavailable.")
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
        embed.add_field(name="Sample of Running Trains", value=sample_text, inline=False)
      embed.set_footer(text="Data source: Iarnród Éireann REST API v1")
      await ctx.send(embed=embed)

  @train.command(name="info")
  @app_commands.describe(code="The train's 4-character code (e.g., E401)")
  async def train_info(self, ctx: commands.Context, code: str):
    """Get details for a specific train by its code."""
    async with ctx.typing():
      status, data = await self._make_request(f"/trains/{code.upper()}")

      if status == 404 or (data and not data.get("success")):
        err_msg = data.get("errorMessage", f"Train code {code.upper()} not found.") if data else f"Train code {code.upper()} not found."
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

  @train.command(name="movements")
  @app_commands.describe(code="The train's 4-character code (e.g., E401)")
  async def train_movements(self, ctx: commands.Context, code: str):
    """Get movements for a specific train by its code."""
    async with ctx.typing():
      status, data = await self._make_request(f"/trains/{code.upper()}/movements")

      if status == 404 or (data and not data.get("success")):
        err_msg = data.get("errorMessage", f"Movements for train {code.upper()} not found.") if data else f"Movements for train {code.upper()} not found."
        await ctx.send(f"❌ {err_msg}")
        return

      if status != 200 or not data:
        await ctx.send(f"❌ Could not retrieve movements for train {code.upper()}.")
        return

      movements = data.get("movements", data.get("trainMovements", []))
      embed = discord.Embed(
          title=f"🛤️ Train Movements: {code.upper()}",
          description=f"Found **{len(movements)}** recorded movements.",
          color=discord.Color.purple(),
      )

      mov_text = ""
      for m in movements[:8]:
        mov_text += (
            f"• **{m.get('LocationFullName', m.get('location', 'Stop'))}** — "
            f"Arr: {m.get('Arr', 'N/E')} | Dep: {m.get('Dep', 'N/E')}\n"
        )

      if mov_text:
        embed.add_field(name="Recent Stops", value=mov_text, inline=False)
      else:
        embed.add_field(name="Recent Stops", value="No movement details available.", inline=False)

      await ctx.send(embed=embed)

  @train.command(name="hacon")
  async def train_hacon(self, ctx: commands.Context):
    """Get all Hacon trains used by the Irish Rail app."""
    async with ctx.typing():
      status, data = await self._make_request("/hacon-trains")

      if status != 200 or not data:
        await ctx.send("❌ Could not fetch Hacon trains data.")
        return

      trains = data.get("trains", data.get("haconTrains", []))
      embed = discord.Embed(
          title="🚄 Hacon Trains",
          description=f"Loaded **{len(trains)}** Hacon trains.",
          color=discord.Color.teal(),
      )
      
      sample = trains[:5]
      sample_text = ""
      for t in sample:
        sample_text += f"• **{t.get('trainCode', t.get('code', 'N/A'))}**\n"

      if sample_text:
        embed.add_field(name="Sample Hacon Trains", value=sample_text, inline=False)

      await ctx.send(embed=embed)

  # --- Station Commands Group ---

  @commands.hybrid_group(name="station", aliases=["stations"])
  async def station(self, ctx: commands.Context):
    """Irish Rail station commands."""
    if ctx.invoked_subcommand is None:
      await ctx.send_help()

  @station.command(name="lookup")
  @app_commands.describe(name="The station name to search for (e.g., Connolly, Cork)")
  async def station_lookup(self, ctx: commands.Context, *, name: str):
    """Search for a station name to find its station code/ID."""
    async with ctx.typing():
      status, data = await self._make_request("/stations")

      if status != 200 or not data or not data.get("success"):
        await ctx.send("❌ Could not fetch station database.")
        return

      stations = data.get("stations", [])
      query = name.lower()
      
      # Find matches based on name or alias containing the query string
      matches = [
          s for s in stations 
          if query in s.get("name", "").lower() or query in s.get("alias", "").lower()
      ]

      if not matches:
        await ctx.send(f"❌ No stations found matching **'{name}'**.")
        return

      embed = discord.Embed(
          title=f"🔍 Station Lookup: '{name}'",
          description=f"Found **{len(matches)}** matching station(s):",
          color=discord.Color.blurple(),
      )

      match_text = ""
      for m in matches[:10]: # Limit to 10 matches to avoid embed limits
        match_text += f"• **{m.get('name')}** — Code: `{m.get('code')}`"
        if m.get('alias'):
          match_text += f" *(Alias: {m.get('alias')})*"
        match_text += "\n"

      embed.add_field(name="Results", value=match_text, inline=False)
      await ctx.send(embed=embed)

  @station.command(name="all")
  @app_commands.describe(station_type="Filter stations by type (D, S, A)")
  async def station_all(self, ctx: commands.Context, station_type: str = None):
    """Get all stations operated by Irish Rail."""
    async with ctx.typing():
      params = {"type": station_type.upper()} if station_type else None
      status, data = await self._make_request("/stations", params=params)

      if status != 200 or not data or not data.get("success"):
        await ctx.send("❌ Could not fetch stations list.")
        return

      stations = data.get("stations", [])
      embed = discord.Embed(
          title="🏢 Irish Rail Stations",
          description=f"Found **{len(stations)}** stations across the network.",
          color=discord.Color.gold(),
      )

      sample = stations[:8]
      sample_text = ""
      for s in sample:
        sample_text += f"• **{s.get('code')}**: {s.get('name')}\n"

      if sample_text:
        embed.add_field(name="Sample Stations", value=sample_text, inline=False)
      
      await ctx.send(embed=embed)

  @station.command(name="info")
  @app_commands.describe(code="The 5-character station code (e.g., CNLLY)")
  async def station_info(self, ctx: commands.Context, code: str):
    """Get details for a specific station by its code."""
    async with ctx.typing():
      status, data = await self._make_request(f"/stations/{code.upper()}")

      if status == 404 or (data and not data.get("success")):
        err_msg = data.get("errorMessage", f"No station found matching code '{code.upper()}'") if data else f"No station found matching code '{code.upper()}'"
        await ctx.send(f"❌ {err_msg}")
        return

      if status != 200 or not data or "station" not in data:
        await ctx.send(f"❌ Could not retrieve details for station **{code.upper()}**.")
        return

      s = data["station"]
      embed = discord.Embed(
          title=f"🏢 Station: {s.get('name')} ({s.get('code')})",
          color=discord.Color.gold(),
      )
      embed.add_field(name="Alias", value=s.get("alias", "N/A"), inline=False)
      embed.add_field(name="Latitude", value=str(s.get("latitude", "N/A")), inline=True)
      embed.add_field(name="Longitude", value=str(s.get("longitude", "N/A")), inline=True)

      await ctx.send(embed=embed)

  @station.command(name="timetable")
  @app_commands.describe(code="The 5-character station code (e.g., CNLLY)")
  async def station_timetable(self, ctx: commands.Context, code: str):
    """Get the live timetable for a specific station code."""
    async with ctx.typing():
      status, data = await self._make_request(f"/stations/{code.upper()}/timetable")

      if status == 404 or (data and not data.get("success")):
        err_msg = data.get("errorMessage", f"No station found matching code '{code.upper()}'") if data else f"No station found matching code '{code.upper()}'"
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

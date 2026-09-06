import aiohttp
import discord
from redbot.core import Config, app_commands, commands


class StationSelectView(discord.ui.View):
  """A view with a dropdown select menu for station disambiguation."""

  def __init__(self, cog, ctx, matches, callback_func, *args, **kwargs):
    super().__init__(timeout=60)
    self.cog = cog
    self.ctx = ctx
    self.callback_func = callback_func
    self.args = args
    self.kwargs = kwargs
    self.selected_code = None

    options = []
    for m in matches[:25]:
      label = m.get("name")[:100]
      code = m.get("code")
      description = f"Code: {code}"
      if m.get("alias"):
        description += f" | Alias: {m.get('alias')}"
      description = description[:100]

      options.append(
          discord.SelectOption(
              label=label, value=code, description=description
          )
      )

    self.select_menu = discord.ui.Select(
        placeholder="Choose the correct station...",
        min_values=1,
        max_values=1,
        options=options,
    )
    self.select_menu.callback = self.select_callback
    self.add_item(self.select_menu)

  async def select_callback(self, interaction: discord.Interaction):
    if interaction.user.id != self.ctx.author.id:
      await interaction.response.send_message(
          "❌ You are not allowed to use this menu.", ephemeral=True
      )
      return

    self.selected_code = self.select_menu.values[0]
    
    for item in self.children:
      item.disabled = True
    
    await interaction.response.edit_message(
        content=f"✅ Selected station code: **{self.selected_code}**. Loading...",
        view=self,
    )
    
    self.stop()
    await self.callback_func(self.ctx, self.selected_code, *self.args, **self.kwargs)

  async def on_timeout(self):
    for item in self.children:
      item.disabled = True
    try:
      await self.message.edit(content="⌛ Station selection timed out.", view=self)
    except Exception:
      pass


class Train(commands.Cog):
  """Interact with the Iarnród Éireann (Irish Rail) REST API v1."""

  def __init__(self, bot):
    self.bot = bot
    self.base_url = "https://ie.api.thediabetic.dev"
    
    self.config = Config.get_conf(
        self, identifier=492089091320446976, force_registration=True
    )
    default_global = {"user_agent": "Red-DiscordBot (IrishRail Cog)"}
    self.config.register_global(**default_global)

  async def _get_headers(self) -> dict:
    ua = await self.config.user_agent()
    return {
        "User-Agent": ua,
        "Accept": "application/json"
    }

  async def _make_request(self, endpoint: str, params: dict = None):
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

  async def _resolve_station(self, ctx: commands.Context, query: str, callback_func, *args, **kwargs):
    query_clean = query.strip().lower()
    
    status, data = await self._make_request("/stations")
    if status != 200 or not data or not data.get("success"):
      return query.upper()

    stations = data.get("stations", [])
    
    for s in stations:
      if s.get("code", "").lower() == query_clean:
        return s.get("code")

    matches = [
        s for s in stations 
        if query_clean in s.get("name", "").lower() or query_clean in s.get("alias", "").lower()
    ]

    if not matches:
      await ctx.send(f"❌ No stations found matching **'{query}'**.")
      return None

    if len(matches) == 1:
      return matches[0].get("code")

    embed = discord.Embed(
        title=f"⚠️ Multiple Stations Found for '{query}'",
        description="Please select the correct station from the dropdown menu below:",
        color=discord.Color.orange(),
    )
    
    view = StationSelectView(self, ctx, matches, callback_func, *args, **kwargs)
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg
    return None

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
      for m in matches[:10]:
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

  async def _do_station_info(self, ctx: commands.Context, code: str):
    """Worker logic for station info after resolution."""
    async with ctx.typing():
      status, data = await self._make_request(f"/stations/{code}")

      if status == 404 or (data and not data.get("success")):
        err_msg = data.get("errorMessage", f"No station found matching code '{code}'") if data else f"No station found matching code '{code}'"
        await ctx.send(f"❌ {err_msg}")
        return

      if status != 200 or not data or not data.get("station"):
        await ctx.send(f"❌ Could not retrieve details for station **{code}**.")
        return

      s = data["station"]
      embed = discord.Embed(
          title=f"🏢 Station: {s.get('name', 'Unknown')} ({s.get('code', code)})",
          color=discord.Color.gold(),
      )
      embed.add_field(name="Alias", value=s.get("alias", "N/A"), inline=False)
      embed.add_field(name="Latitude", value=str(s.get("latitude", "N/A")), inline=True)
      embed.add_field(name="Longitude", value=str(s.get("longitude", "N/A")), inline=True)

      await ctx.send(embed=embed)

  @station.command(name="info")
  @app_commands.describe(station_query="The station code or name (e.g., CNLLY or Connolly)")
  async def station_info(self, ctx: commands.Context, *, station_query: str):
    """Get details for a specific station by its code or name."""
    code = await self._resolve_station(ctx, station_query, self._do_station_info)
    if code:
      await self._do_station_info(ctx, code)

  async def _do_station_timetable(self, ctx: commands.Context, code: str):
    """Worker logic for station timetable after resolution."""
    async with ctx.typing():
      status, data = await self._make_request(f"/stations/{code}/timetable")

      if status == 404 or (data and not data.get("success")):
        err_msg = data.get("errorMessage", f"No station found matching code '{code}'") if data else f"No station found matching code '{code}'"
        await ctx.send(f"❌ {err_msg}")
        return

      if status != 200 or not data or "timetable" not in data:
        await ctx.send(f"❌ Could not retrieve timetable for station **{code}**.")
        return

      timetable = data["timetable"]
      embed = discord.Embed(
          title=f"🕒 Timetable for Station: {code}",
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

  @station.command(name="timetable")
  @app_commands.describe(station_query="The station code or name (e.g., CNLLY or Connolly)")
  async def station_timetable(self, ctx: commands.Context, *, station_query: str):
    """Get the live timetable for a specific station by code or name."""
    code = await self._resolve_station(ctx, station_query, self._do_station_timetable)
    if code:
      await self._do_station_timetable(ctx, code)



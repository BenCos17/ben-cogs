"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

import discord
import asyncio
import re
import datetime
import aiohttp
from discord.ext import tasks, commands
from redbot.core import commands as red_commands, Config
import typing

from .data.icao_codes import (
    law_enforcement_icao_set, military_icao_set, medical_icao_set, 
    suspicious_icao_set, newsagency_icao_set, balloons_icao_set, 
    global_prior_known_accident_set, ukr_conflict_set, agri_utility_set
)
from .utils.api import APIManager
from .utils.helpers import HelperUtils
from .utils.export import ExportManager
from .commands.aircraft import AircraftCommands
from .commands.airport import AirportCommands
from .commands.admin import AdminCommands


def dashboard_page(*args, **kwargs):
    def decorator(func):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator

class Skysearch(red_commands.Cog):
    """SkySearch - Aircraft tracking and information cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.config.register_global(airplanesliveapi=None)  # API key for airplanes.live
        self.config.register_global(openweathermap_api=None)  # OWM API key
        self.config.register_global(api_mode="primary")  # API mode: 'primary' or 'fallback (going to remove this when airplanes.live removes the public api because of companies abusing it...when that happens you'll need an api key for it)'
        self.config.register_guild(alert_channel=None, alert_role=None, auto_icao=False, last_emergency_squawk_time=None, auto_delete_not_found=True)
        
        # Initialize utility managers
        self.api = APIManager(self)
        self.helpers = HelperUtils(self)
        self.export = ExportManager(self)
        
        # Initialize command modules
        self.aircraft_commands = AircraftCommands(self)
        self.airport_commands = AirportCommands(self)
        self.admin_commands = AdminCommands(self)
        
        # Initialize ICAO sets
        self.law_enforcement_icao_set = law_enforcement_icao_set
        self.military_icao_set = military_icao_set
        self.medical_icao_set = medical_icao_set
        self.suspicious_icao_set = suspicious_icao_set
        self.newsagency_icao_set = newsagency_icao_set
        self.balloons_icao_set = balloons_icao_set
        self.global_prior_known_accident_set = global_prior_known_accident_set
        self.ukr_conflict_set = ukr_conflict_set
        self.agri_utility_set = agri_utility_set
        
        # Start background tasks
        self.check_emergency_squawks.start()
        
    async def cog_unload(self):
        """Clean up when the cog is unloaded."""
        await self.api.close()

    @red_commands.guild_only()
    @red_commands.group(name='skysearch', help='Core menu for the cog', invoke_without_command=True)
    async def skysearch(self, ctx):
        """SkySearch command group"""
        embed = discord.Embed(title="Thanks for using SkySearch", description="SkySearch is a powerful, easy-to-use OSINT tool for tracking aircraft.", color=0xfffffe)
        embed.add_field(name="aircraft", value="Use `aircraft` to show available commands to fetch information about live aircraft and configure emergency squawk alerts.", inline=False)
        embed.add_field(name="airport", value="Use `airport` to show available commands to fetch information and imagery of airports around the world.", inline=False)
        await ctx.send(embed=embed)
    
    @red_commands.guild_only()
    @skysearch.command(name='stats', help='Get statistics about SkySearch and the data used here')
    async def stats(self, ctx):
        """Get SkySearch statistics."""
        url = "https://api.airplanes.live/stats"

        try:
            if not hasattr(self, '_http_client'):
                self._http_client = aiohttp.ClientSession()
            async with self._http_client.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    raise aiohttp.ClientError(f"API responded with status code: {response.status}")

            embed = discord.Embed(title="SkySearch Statistics", description="Consolidated statistics and data sources for SkySearch.", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")

            if "beast" in data:
                embed.add_field(name="Beast", value="**{}** feeders".format("{:,}".format(data["beast"])), inline=True)
            if "mlat" in data:
                embed.add_field(name="MLAT", value="**{}** feeders".format("{:,}".format(data["mlat"])), inline=True)
            if "other" in data:
                embed.add_field(name="Other Freq's", value="**{}** feeders".format("{:,}".format(data["other"])), inline=True)
            if "aircraft" in data:
                embed.add_field(name="Aircraft tracked right now", value="**{}** aircraft".format("{:,}".format(data["aircraft"])), inline=False)

            embed.add_field(name="This data appears in the following commands", value="`callsign` `icao` `reg` `squawk` `type` `radius` `pia` `mil` `ladd` `export`", inline=False)

            embed.add_field(name="Law enforcement aircraft", value="**{:,}** tagged".format(len(self.law_enforcement_icao_set)), inline=True)
            embed.add_field(name="Military & government aircraft", value="**{:,}** tagged".format(len(self.military_icao_set)), inline=True)
            embed.add_field(name="Medical aircraft", value="**{:,}** tagged".format(len(self.medical_icao_set)), inline=True)
            embed.add_field(name="Media aircraft", value="**{:,}** known".format(len(self.newsagency_icao_set)), inline=True)
            embed.add_field(name="Damaged aircraft", value="**{:,}** known".format(len(self.global_prior_known_accident_set)), inline=True)
            embed.add_field(name="Wartime aircraft", value="**{:,}** observed".format(len(self.ukr_conflict_set)), inline=True)
            embed.add_field(name="Utility aircraft", value="**{:,}** spotted".format(len(self.agri_utility_set)), inline=True)
            embed.add_field(name="Balloons", value="**{:,}** known".format(len(self.balloons_icao_set)), inline=True)
            embed.add_field(name="Suspicious aircraft", value="**{:,}** identifiers".format(len(self.suspicious_icao_set)), inline=True)
            embed.add_field(name="This data appears in the following commands", value="`callsign` `icao` `reg` `squawk` `type` `radius` `pia` `mil` `ladd`", inline=False)
            embed.add_field(name="Other services", value="Additional data used in this cog is shown below", inline=False)
            embed.add_field(name="Photography", value="Photos are powered by community contributions at [planespotters.net](https://www.planespotters.net/)", inline=True)
            embed.add_field(name="Airport data", value="Airport data is powered by the [airport-data.com](https://airport-data.com/) API service", inline=True)
            embed.add_field(name="Runway data", value="Runway data is powered by the [airportdb.io](https://airportdb.io) API service", inline=True)
            embed.add_field(name="Mapping and imagery", value="Mapping and ground imagery powered by [Google Maps](https://maps.google.com) and the [Maps Static API](https://developers.google.com/maps/documentation/maps-static)", inline=False)

            await ctx.send(embed=embed)
        except aiohttp.ClientError as e:
            embed = discord.Embed(title="Error", description=f"Error fetching data: {e}", color=0xff4545)
            await ctx.send(embed=embed)

    # Aircraft commands
    @red_commands.guild_only()
    @red_commands.group(name='aircraft', help='Command center for aircraft related commands', invoke_without_command=True)
    async def aircraft_group(self, ctx):
        """Command center for aircraft related commands"""
        embed = discord.Embed(title="Aircraft Commands", description="Available aircraft-related commands:", color=0xfffffe)
        embed.add_field(name="Search Commands", value="`icao` `callsign` `reg` `type` `squawk` `radius` `closest`", inline=False)
        embed.add_field(name="Special Aircraft", value="`military` `ladd` `pia`", inline=False)
        embed.add_field(name="Export", value="`export` - Export aircraft data to CSV, PDF, TXT, or HTML", inline=False)
        embed.add_field(name="Configuration", value="`alertchannel` `alertrole` `autoicao` `autodelete` `showalertchannel` `setapimode` `apimode`", inline=False)
        embed.add_field(name="Other", value="`scroll` - Scroll through available planes", inline=False)
        # Only show debug command to bot owners
        if await ctx.bot.is_owner(ctx.author):
            embed.add_field(name="Debug", value="`debugapi` - Debug API issues (owner only)\n`debugtoggle` - Toggle debug output for lookups (owner only)\n`debug` - Run a debug lookup (owner only)", inline=False)
        embed.add_field(name="Detailed Help", value="Use `*help aircraft` for detailed command information", inline=False)
        await ctx.send(embed=embed)

    # Delegate aircraft commands to the aircraft module
    @aircraft_group.command(name='icao')
    async def aircraft_icao(self, ctx, hex_id: str):
        """Get aircraft information by ICAO hex code."""
        await self.aircraft_commands.aircraft_by_icao(ctx, hex_id)

    @aircraft_group.command(name='callsign')
    async def aircraft_callsign(self, ctx, callsign: str):
        """Get aircraft information by callsign."""
        await self.aircraft_commands.aircraft_by_callsign(ctx, callsign)

    @aircraft_group.command(name='reg')
    async def aircraft_reg(self, ctx, registration: str):
        """Get aircraft information by registration."""
        await self.aircraft_commands.aircraft_by_reg(ctx, registration)

    @aircraft_group.command(name='type')
    async def aircraft_type(self, ctx, aircraft_type: str):
        """Get aircraft information by type."""
        await self.aircraft_commands.aircraft_by_type(ctx, aircraft_type)

    @aircraft_group.command(name='squawk')
    async def aircraft_squawk(self, ctx, squawk_value: str):
        """Get aircraft information by squawk code."""
        await self.aircraft_commands.aircraft_by_squawk(ctx, squawk_value)

    @aircraft_group.command(name='export')
    async def aircraft_export(self, ctx, search_type: str, search_value: str, file_format: str):
        """Export aircraft data to various formats."""
        await self.aircraft_commands.export_aircraft(ctx, search_type, search_value, file_format)

    @aircraft_group.command(name='military')
    async def aircraft_military(self, ctx):
        """Get information about military aircraft."""
        await self.aircraft_commands.show_military_aircraft(ctx)

    @aircraft_group.command(name='ladd')
    async def aircraft_ladd(self, ctx):
        """Get information on LADD-restricted aircraft."""
        await self.aircraft_commands.ladd_aircraft(ctx)

    @aircraft_group.command(name='pia')
    async def aircraft_pia(self, ctx):
        """View live aircraft using private ICAO addresses."""
        await self.aircraft_commands.pia_aircraft(ctx)

    @aircraft_group.command(name='radius')
    async def aircraft_radius(self, ctx, lat: str, lon: str, radius: str):
        """Get information about aircraft within a specified radius."""
        await self.aircraft_commands.aircraft_within_radius(ctx, lat, lon, radius)

    @aircraft_group.command(name='closest')
    async def aircraft_closest(self, ctx, lat: str, lon: str, radius: str = "100"):
        """Find the closest aircraft to specified coordinates."""
        await self.aircraft_commands.closest_aircraft(ctx, lat, lon, radius)

    @aircraft_group.command(name='scroll')
    async def aircraft_scroll(self, ctx, category: str = 'mil'):
        """Scroll through available planes. Optionally specify a category: mil, ladd, pia, or all."""
        await self.aircraft_commands.scroll_planes(ctx, category)

    # Admin commands
    @aircraft_group.command(name='alertchannel')
    async def aircraft_alertchannel(self, ctx, channel: discord.TextChannel = None):
        """Set or clear a channel to send emergency squawk alerts to."""
        await self.admin_commands.set_alert_channel(ctx, channel)

    @aircraft_group.command(name='alertrole')
    async def aircraft_alertrole(self, ctx, role: discord.Role = None):
        """Set or clear a role to mention when new emergency squawks occur."""
        await self.admin_commands.set_alert_role(ctx, role)

    @aircraft_group.command(name='autoicao')
    async def aircraft_autoicao(self, ctx, state: bool = None):
        """Enable or disable automatic ICAO lookup."""
        await self.admin_commands.autoicao(ctx, state)

    @aircraft_group.command(name='autodelete', aliases=['autodel'])
    async def aircraft_autodelete(self, ctx, state: bool = None):
        """Enable or disable automatic deletion of 'not found' messages."""
        await self.admin_commands.autodelete(ctx, state)

    @aircraft_group.command(name='showalertchannel')
    async def aircraft_showalertchannel(self, ctx):
        """Show alert task status and output if set."""
        await self.admin_commands.list_alert_channels(ctx)

    @red_commands.is_owner()
    @aircraft_group.command(name='debugapi')
    async def aircraft_debugapi(self, ctx):
        """Debug API key and connection issues (DM only)."""
        await self.admin_commands.debug_api(ctx)

    @red_commands.is_owner()
    @aircraft_group.command(name='setapimode')
    async def aircraft_set_api_mode(self, ctx, mode: str):
        """Set which API to use globally: 'primary' or 'fallback'. (owner only)"""
        mode = mode.lower()
        if mode not in ("primary", "fallback"):
            await ctx.send("❌ Invalid mode. Use 'primary' or 'fallback'.")
            return
        await self.config.api_mode.set(mode)
        await ctx.send(f"✅ API mode set to **{mode}**.")

    @red_commands.is_owner()
    @aircraft_group.command(name='apimode')
    async def aircraft_show_api_mode(self, ctx):
        """Show the current global API mode. (owner only)"""
        mode = await self.config.api_mode()
        await ctx.send(f"🌐 Current API mode: **{mode}**")

    @red_commands.is_owner()
    @aircraft_group.command(name='debug')
    async def aircraft_debug_lookup(self, ctx, lookup_type: str = None, value: str = None):
        """Debug an aircraft lookup: *aircraft debug <lookup_type> <value> (lookup_type: icao, callsign, reg, type, squawk)"""
        if not lookup_type or not value:
            await ctx.send("Usage: `*aircraft debug <lookup_type> <value>` (lookup_type: icao, callsign, reg, type, squawk)")
            return
        lookup_type = lookup_type.lower()
        if lookup_type not in ("icao", "callsign", "reg", "type", "squawk"):
            await ctx.send("Invalid lookup_type. Must be one of: icao, callsign, reg, type, squawk.")
            return
        await self.aircraft_commands.debug_lookup(ctx, lookup_type, value)

    @red_commands.is_owner()
    @aircraft_group.command(name='debugtoggle')
    async def aircraft_debugtoggle(self, ctx, state: str = None):
        """Enable or disable aircraft debug output: *aircraft debugtoggle <on|off>"""
        if state is None or state.lower() not in ("on", "off"):
            await ctx.send("Usage: `*aircraft debugtoggle <on|off>`")
            return
        enabled = state.lower() == "on"
        await self.aircraft_commands.set_debug(ctx, enabled)

    # Airport commands
    @red_commands.guild_only()
    @red_commands.group(name='airport', help='Command center for airport related commands', invoke_without_command=True)
    async def airport_group(self, ctx):
        """Command center for airport related commands"""
        embed = discord.Embed(title="Airport Commands", description="Available airport-related commands:", color=0xfffffe)
        embed.add_field(name="Information", value="`info` - Get airport information by ICAO/IATA code", inline=False)
        embed.add_field(name="Details", value="`runway` - Get runway information\n`navaid` - Get navigational aids\n`forecast` - Get weather forecast", inline=False)
        embed.add_field(name="Detailed Help", value="Use `*help airport` for detailed command information", inline=False)
        await ctx.send(embed=embed)

    # Delegate airport commands to the airport module
    @airport_group.command(name='info')
    async def airport_info(self, ctx, airport_code: str):
        """Get airport information by ICAO or IATA code."""
        await self.airport_commands.airport_info(ctx, airport_code)

    @airport_group.command(name='runway')
    async def airport_runway(self, ctx, airport_code: str):
        """Get runway information for an airport."""
        await self.airport_commands.runway_info(ctx, airport_code)

    @airport_group.command(name='navaid')
    async def airport_navaid(self, ctx, airport_code: str):
        """Get navigational aids for an airport."""
        await self.airport_commands.navaid_info(ctx, airport_code)

    @airport_group.command(name='forecast', help='Get the weather for an airport by ICAO or IATA code (US airports only).')
    async def airport_forecast(self, ctx, code: str):
        """Get the weather for an airport by ICAO or IATA code (US airports only)."""
        await self.airport_commands.forecast(ctx, code)

    # Owner commands
    @red_commands.is_owner()
    @red_commands.command(name='setapikey')
    async def setapikey(self, ctx, api_key: str):
        """Set the airplanes.live API key."""
        await self.admin_commands.set_api_key(ctx, api_key)

    @red_commands.is_owner()
    @red_commands.command(name='apikey')
    async def apikey(self, ctx):
        """Check the status of the API key configuration."""
        await self.admin_commands.check_api_key(ctx)

    @red_commands.is_owner()
    @red_commands.command(name='clearapikey')
    async def clearapikey(self, ctx):
        """Clear the API key configuration."""
        await self.admin_commands.clear_api_key(ctx)

    @red_commands.is_owner()
    @red_commands.command(name='setowmkey')
    async def set_owm_key(self, ctx, api_key: str):
        """Set the OpenWeatherMap API key."""
        await self.config.openweathermap_api.set(api_key)
        await ctx.send("OpenWeatherMap API key set.")

    @red_commands.is_owner()
    @red_commands.command(name='owmkey')
    async def show_owm_key(self, ctx):
        """Show the current OpenWeatherMap API key (partially masked)."""
        key = await self.config.openweathermap_api()
        if key:
            await ctx.send(f"OpenWeatherMap API key: `{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}`")
        else:
            await ctx.send("No OpenWeatherMap API key set.")

    @red_commands.is_owner()
    @red_commands.command(name='clearowmkey')
    async def clear_owm_key(self, ctx):
        """Clear the OpenWeatherMap API key."""
        await self.config.openweathermap_api.set(None)
        await ctx.send("OpenWeatherMap API key cleared.")

    @tasks.loop(minutes=2)
    async def check_emergency_squawks(self):
        """Background task to check for emergency squawks."""
        try:
            emergency_squawk_codes = ['7500', '7600', '7700']
            for squawk_code in emergency_squawk_codes:
                # Use new REST API endpoint for squawk filter - must combine with base query
                url = f"{self.api.api_url}/?all_with_pos&filter_squawk={squawk_code}"
                response = await self.api.make_request(url)  # No ctx for background task
                if response and 'aircraft' in response:
                    for aircraft_info in response['aircraft']:
                        # Ignore aircraft with the hex 00000000
                        if aircraft_info.get('hex') == '00000000':
                            continue
                        guilds = self.bot.guilds
                        for guild in guilds:
                            alert_channel_id = await self.config.guild(guild).alert_channel()
                            if alert_channel_id:
                                alert_channel = self.bot.get_channel(alert_channel_id)
                                if alert_channel:
                                    # Get the alert role
                                    alert_role_id = await self.config.guild(guild).alert_role()
                                    alert_role_mention = f"<@&{alert_role_id}>" if alert_role_id else ""
                                    
                                    # Send the new alert with role mention if available
                                    if alert_role_mention:
                                        await alert_channel.send(alert_role_mention, allowed_mentions=discord.AllowedMentions(roles=True))
                                    await self.aircraft_commands.send_aircraft_info(alert_channel, {'aircraft': [aircraft_info]})
                                    
                                    # Check if aircraft has landed
                                    if aircraft_info.get('altitude') is not None and aircraft_info.get('altitude') < 25:
                                        embed = discord.Embed(title="Aircraft landed", description=f"Aircraft {aircraft_info.get('hex')} has landed while squawking {squawk_code}.", color=0x00ff00)
                                        await alert_channel.send(embed=embed)
                                else:
                                    # Only log if channel was set but not found (actual error)
                                    print(f"Warning: Alert channel {alert_channel_id} not found for guild {guild.name} - channel may have been deleted")
                            # Removed the "No alert channel set" message - this is normal behavior
                await asyncio.sleep(2)  # Add a delay to respect API rate limit
        except Exception as e:
            print(f"Error checking emergency squawks: {e}")

    @check_emergency_squawks.before_loop
    async def before_check_emergency_squawks(self):
        """Wait for bot to be ready before starting the task."""
        await self.bot.wait_until_ready()

    @red_commands.Cog.listener()
    async def on_message(self, message):
        """Handle automatic ICAO lookup."""
        if message.author == self.bot.user:
            return

        if message.guild is None:
            return

        auto_icao = await self.config.guild(message.guild).auto_icao()
        if not auto_icao:
            return

        content = message.content
        icao_pattern = re.compile(r'^[a-fA-F0-9]{6}$')

        if icao_pattern.match(content):
            ctx = await self.bot.get_context(message)
            await self.aircraft_commands.aircraft_by_icao(ctx, content)

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

    @dashboard_page(name=None, description="SkySearch Dashboard Home", methods=("GET",), is_owner=False)
    async def dashboard_home(self, user: discord.User, **kwargs) -> typing.Dict[str, typing.Any]:
        source = '<h2>Welcome to the SkySearch Dashboard Integration!</h2>' \
                 '<p>This page is provided by the SkySearch cog. Use the navigation to explore available features.</p>'
        return {
            "status": 0,
            "web_content": {"source": source},
        }

    @dashboard_page(name="guild", description="View SkySearch info for a guild", methods=("GET",), is_owner=False)
    async def guild_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        source = f'<h4>SkySearch is active in guild: <b>{guild.name}</b> (ID: {guild.id})</h4>'
        return {
            "status": 0,
            "web_content": {"source": source},
        }

    @dashboard_page(name="settings", description="Configure SkySearch settings for this guild", methods=("GET", "POST"), is_owner=False)
    async def guild_settings_page(self, user: discord.User, guild: discord.Guild, request: typing.Optional[dict] = None, **kwargs) -> typing.Dict[str, typing.Any]:
        config = self.config.guild(guild)
        updates = []
        try:
            if request and (request.get("method") == "POST" or request.get("_method") == "POST"):
                data = request.get("data", request)
                channel_id = data.get("alert_channel")
                if channel_id is not None:
                    try:
                        if channel_id == "":
                            await config.alert_channel.clear()
                            updates.append("Alert channel cleared.")
                        else:
                            await config.alert_channel.set(int(channel_id))
                            updates.append(f"Alert channel set to <#{channel_id}>.")
                    except Exception as e:
                        updates.append(f"Error setting alert channel: {e}")
                role_id = data.get("alert_role")
                if role_id is not None:
                    try:
                        if role_id == "":
                            await config.alert_role.clear()
                            updates.append("Alert role cleared.")
                        else:
                            await config.alert_role.set(int(role_id))
                            updates.append(f"Alert role set to <@&{role_id}>.")
                    except Exception as e:
                        updates.append(f"Error setting alert role: {e}")
                # Fix checkbox handling: if not present, set to False
                auto_icao = data.get("auto_icao") is not None
                try:
                    await config.auto_icao.set(auto_icao)
                    updates.append(f"Auto ICAO lookup set to {auto_icao}.")
                except Exception as e:
                    updates.append(f"Error setting auto ICAO: {e}")
                auto_delete = data.get("auto_delete_not_found") is not None
                try:
                    await config.auto_delete_not_found.set(auto_delete)
                    updates.append(f"Auto-delete 'not found' set to {auto_delete}.")
                except Exception as e:
                    updates.append(f"Error setting auto-delete: {e}")
        except Exception:
            pass
        alert_channel = await config.alert_channel()
        alert_role = await config.alert_role()
        auto_icao = await config.auto_icao()
        auto_delete = await config.auto_delete_not_found()
        updates_html = f"<div style='color:green;'>{'<br>'.join(updates)}</div>" if updates else ""
        source = f'''
        <h3>SkySearch Guild Settings</h3>
        {updates_html}
        <form method="post">
            <label>Alert Channel ID:<br><input type="text" name="alert_channel" value="{alert_channel or ''}" placeholder="Channel ID or blank to clear"></label><br>
            <label>Alert Role ID:<br><input type="text" name="alert_role" value="{alert_role or ''}" placeholder="Role ID or blank to clear"></label><br>
            <label>Auto ICAO Lookup:<br><input type="checkbox" name="auto_icao" {'checked' if auto_icao else ''}></label><br>
            <label>Auto-Delete 'Not Found' Messages:<br><input type="checkbox" name="auto_delete_not_found" {'checked' if auto_delete else ''}></label><br>
            <button type="submit">Update Settings</button>
        </form>
        '''
        return {
            "status": 0,
            "web_content": {"source": source},
        }

    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        try:
            self.check_emergency_squawks.cancel()
        except Exception as e:
            print(f"Error unloading cog: {e}")
        
        
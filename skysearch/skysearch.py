"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

import discord
import asyncio
import re
import datetime
import aiohttp
import time
import json
import urllib.parse
import logging
from redbot.core import commands, Config
from redbot.core.i18n import Translator, cog_i18n, set_contextual_locales_from_guild
from discord.ext import tasks

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
from .dashboard.dashboard_integration import DashboardIntegration
from .api.squawk_api import SquawkAlertAPI
from .api.command_api import CommandAPI

log = logging.getLogger("red.skysearch")


# Internationalization
_ = Translator("Skysearch", __file__)


@cog_i18n(_)
class Skysearch(commands.Cog, DashboardIntegration):
    """SkySearch - Aircraft tracking and information cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self._skysearch_cog = self  # For dashboard integration access
        self.config = Config.get_conf(self, identifier=492089091320446976)
        self.config.register_global(airplanesliveapi=None)  # API key for airplanes.live
        self.config.register_global(openweathermap_api=None)  # OWM API key
        self.config.register_global(api_mode="primary")  # API mode: 'primary' or 'fallback (going to remove this when airplanes.live removes the public api because of companies abusing it...when that happens you'll need an api key for it)'
        self.config.register_global(api_stats=None)  # API request statistics for persistence
        self.config.register_guild(alert_channel=None, alert_role=None, auto_icao=False, auto_delete_not_found=True, emergency_cooldown=5, last_alerts={}, custom_alerts={})
        
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

        # Squawk alert API
        self.squawk_api = SquawkAlertAPI()

        # Command execution API
        self.command_api = CommandAPI()

    def get_airplane_icon_path(self):
        """Get the path to the local airplane icon."""
        return self.cog_data_folder / "defaultairplane.png"

    def register_squawk_alert_callback(self, callback):
        """
        Register a callback to be called when a squawk alert is triggered.
        The callback should be a coroutine function accepting (guild, aircraft_info, squawk_code).
        """
        self.squawk_api.register_callback(callback)

    def register_command_callback(self, callback):
        """
        Register a callback to be called when a SkySearch command is executed.
        The callback should be a coroutine function accepting (ctx, command_name, args).
        """
        self.command_api.register_callback(callback)

    async def _execute_with_hooks(self, ctx, command_name: str, args: list, command_func):
        """Execute a command with pre/post hooks."""
        import time
        
        # Call basic callbacks
        await self.command_api.call_callbacks(ctx, command_name, args)
        
        # Run pre-execute hooks
        should_continue = await self.command_api.run_pre_execute(ctx, command_name, args)
        if not should_continue:
            return None
            
        # Execute the actual command
        start_time = time.time()
        try:
            result = await command_func()
            success = True
        except Exception as e:
            result = e
            success = False
            raise  # Re-raise the exception
        finally:
            execution_time = time.time() - start_time
            # Run post-execute hooks
            await self.command_api.run_post_execute(ctx, command_name, args, result, execution_time)
            
        return result

    async def cog_unload(self):
        """Clean up when the cog is unloaded."""
        await self.api.close()

    @commands.guild_only()
    @commands.group(name='skysearch', help=_('Core menu for the cog'), invoke_without_command=True)
    async def skysearch(self, ctx):
        """SkySearch command group"""
        embed = discord.Embed(title=_("Thanks for using SkySearch"), description=_("SkySearch is a powerful, easy-to-use OSINT tool for tracking aircraft."), color=0xfffffe)
        embed.add_field(name="aircraft", value=_("Use `aircraft` to show available commands to fetch information about live aircraft and configure emergency squawk alerts."), inline=False)
        embed.add_field(name="airport", value=_("Use `airport` to show available commands to fetch information and imagery of airports around the world."), inline=False)
        embed.add_field(name="📊 API Monitoring", value=_("Use `skysearch apistats` to view API performance and usage statistics"), inline=False)
        await ctx.send(embed=embed)
    
    @commands.guild_only()
    @skysearch.command(name='stats', help=_('Get statistics about SkySearch and the data used here'))
    async def stats(self, ctx):
        """Get SkySearch statistics."""
        data = await self.api.get_stats()

        embed = discord.Embed(title=_("SkySearch Statistics"), description=_("Consolidated statistics and data sources for SkySearch."), color=0xfffffe)
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")

        if data:
            if "beast" in data:
                embed.add_field(name="Beast", value="**{}** feeders".format("{:,}".format(data["beast"])), inline=True)
            if "mlat" in data:
                embed.add_field(name="MLAT", value="**{}** feeders".format("{:,}".format(data["mlat"])), inline=True)
            if "other" in data:
                embed.add_field(name="Other Freq's", value="**{}** feeders".format("{:,}".format(data["other"])), inline=True)
            if "aircraft" in data:
                embed.add_field(name="Aircraft tracked right now", value="**{}** aircraft".format("{:,}".format(data["aircraft"])), inline=False)
        else:
            embed.add_field(name="Aircraft tracked right now", value="?", inline=False)

        embed.add_field(name=_("This data appears in the following commands"), value="`callsign` `icao` `reg` `squawk` `type` `radius` `pia` `mil` `ladd` `export`", inline=False)
        embed.add_field(name=_("Law enforcement aircraft"), value="**{:,}** tagged".format(len(self.law_enforcement_icao_set)), inline=True)
        embed.add_field(name=_("Military & government aircraft"), value="**{:,}** tagged".format(len(self.military_icao_set)), inline=True)
        embed.add_field(name=_("Medical aircraft"), value="**{:,}** tagged".format(len(self.medical_icao_set)), inline=True)
        embed.add_field(name=_("Media aircraft"), value="**{:,}** known".format(len(self.newsagency_icao_set)), inline=True)
        embed.add_field(name=_("Damaged aircraft"), value="**{:,}** known".format(len(self.global_prior_known_accident_set)), inline=True)
        embed.add_field(name=_("Wartime aircraft"), value="**{:,}** observed".format(len(self.ukr_conflict_set)), inline=True)
        embed.add_field(name=_("Utility aircraft"), value="**{:,}** spotted".format(len(self.agri_utility_set)), inline=True)
        embed.add_field(name=_("Balloons"), value="**{:,}** known".format(len(self.balloons_icao_set)), inline=True)
        embed.add_field(name=_("Suspicious aircraft"), value="**{:,}** identifiers".format(len(self.suspicious_icao_set)), inline=True)
        embed.add_field(name=_("This data appears in the following commands"), value="`callsign` `icao` `reg` `squawk` `type` `radius` `pia` `mil` `ladd`", inline=False)
        embed.add_field(name=_("Other services"), value=_("Additional data used in this cog is shown below"), inline=False)
        embed.add_field(name=_("Photography"), value=_("Photos are powered by community contributions at [planespotters.net](https://www.planespotters.net/)"), inline=True)
        embed.add_field(name=_("Airport data"), value=_("Airport data is powered by the [airport-data.com](https://airport-data.com/) API service"), inline=True)
        embed.add_field(name=_("Runway data"), value=_("Runway data is powered by the [airportdb.io](https://airportdb.io) API service"), inline=True)
        embed.add_field(name=_("Mapping and imagery"), value=_("Mapping and ground imagery powered by [Google Maps](https://maps.google.com) and the [Maps Static API](https://developers.google.com/maps/documentation/maps-static)"), inline=False)

        await ctx.send(embed=embed)

    @commands.guild_only()
    @skysearch.command(name='apistats', help=_('View comprehensive API request statistics, performance metrics, and usage analytics'))
    async def apistats(self, ctx):
        """Get detailed API request statistics (delegates to AdminCommands)."""
        await self.admin_commands.apistats(ctx)

    @commands.guild_only()
    @commands.is_owner()
    @skysearch.command(name='apistats_reset', help=_('Reset API request statistics (owner only)'))
    async def apistats_reset(self, ctx):
        """Reset API request statistics (delegates to AdminCommands)."""
        await self.admin_commands.apistats_reset(ctx)

    @commands.guild_only()
    @commands.is_owner()
    @skysearch.command(name='apistats_save', help=_('Manually save API statistics to config (owner only)'))
    async def apistats_save(self, ctx):
        """Manually save API statistics to config (delegates to AdminCommands)."""
        await self.admin_commands.apistats_save(ctx)

    @commands.guild_only()
    @commands.is_owner()
    @skysearch.command(name='apistats_config', help=_('View API statistics auto-save configuration and current status (owner only)'))
    async def apistats_config(self, ctx):
        """View API statistics saving configuration (delegates to AdminCommands)."""
        await self.admin_commands.apistats_config(ctx)

    @commands.guild_only()
    @commands.is_owner()
    @skysearch.command(name='apistats_debug', help=_('Debug API statistics data structure and time-based data (owner only)'))
    async def apistats_debug(self, ctx):
        """Debug API statistics data structure (delegates to AdminCommands)."""
        await self.admin_commands.apistats_debug(ctx)

    # Aircraft commands
    @commands.guild_only()
    @commands.group(name='aircraft', help=_('Command center for aircraft related commands and API monitoring'), invoke_without_command=True)
    async def aircraft_group(self, ctx):
        """Command center for aircraft related commands and API monitoring"""
        embed = discord.Embed(title=_("Aircraft Commands"), description=_("Available aircraft-related commands and API monitoring:"), color=0xfffffe)
        embed.add_field(name=_("Search Commands"), value="`icao` `callsign` `reg` `type` `squawk` `radius` `closest`", inline=False)
        embed.add_field(name=_("Special Aircraft"), value="`military` `ladd` `pia`", inline=False)
        embed.add_field(name=_("Export"), value=_("`export` - Export aircraft data to CSV, PDF, TXT, or HTML"), inline=False)
        embed.add_field(name=_("Configuration"), value="`alertchannel` `alertrole` `autoicao` `autodelete` `showalertchannel` `setapimode` `apimode`", inline=False)
        embed.add_field(name=_("Custom Alerts"), value="`addalert` `removealert` `listalerts` `clearalerts`\n*Use `addalert` with optional channel parameter*", inline=False)
        embed.add_field(name=_("Other"), value=_("`scroll` - Scroll through available planes\n`feeder` - Parse feeder JSON data (secure modal)"), inline=False)
        # Only show debug command to bot owners
        if await ctx.bot.is_owner(ctx.author):
            embed.add_field(name=_("Debug"), value=_("`debugapi` - Debug API issues (owner only)\n`debugtoggle` - Toggle debug output for lookups (owner only)\n`debug` - Run a debug lookup (owner only)"), inline=False)
        embed.add_field(name="📊 API Monitoring", value=_("Use `skysearch apistats` to view API performance and usage statistics"), inline=False)
        embed.add_field(name=_("Detailed Help"), value=_("Use `*help aircraft` for detailed command information"), inline=False)
        await ctx.send(embed=embed)

    # Delegate aircraft commands to the aircraft module
    @aircraft_group.command(name='icao')
    async def aircraft_icao(self, ctx, hex_id: str):
        """Get aircraft information by ICAO hex code."""
        await self._execute_with_hooks(
            ctx, 'aircraft_icao', [hex_id],
            lambda: self.aircraft_commands.aircraft_by_icao(ctx, hex_id)
        )

    @aircraft_group.command(name='callsign')
    async def aircraft_callsign(self, ctx, callsign: str):
        """Get aircraft information by callsign."""
        await self._execute_with_hooks(
            ctx, 'aircraft_callsign', [callsign],
            lambda: self.aircraft_commands.aircraft_by_callsign(ctx, callsign)
        )

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
        await self._execute_with_hooks(
            ctx, 'aircraft_squawk', [squawk_value],
            lambda: self.aircraft_commands.aircraft_by_squawk(ctx, squawk_value)
        )

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

    @aircraft_group.command(name='feeder')
    async def aircraft_feeder(self, ctx, *, json_input: str = None):
        """Extract feeder URL from JSON data or a URL containing feeder data using secure modal."""
        await self.aircraft_commands.extract_feeder_url(ctx, json_input=json_input)

    # Admin commands
    @aircraft_group.command(name='alertchannel')
    async def aircraft_alertchannel(self, ctx, channel: discord.TextChannel = None):
        """Set or clear a channel to send emergency squawk alerts to."""
        await self.admin_commands.set_alert_channel(ctx, channel)

    @aircraft_group.command(name='alertrole')
    async def aircraft_alertrole(self, ctx, role: discord.Role = None):
        """Set or clear a role to mention when new emergency squawks occur."""
        await self.admin_commands.set_alert_role(ctx, role)

    @aircraft_group.command(name='alertcooldown')
    async def aircraft_alertcooldown(self, ctx, duration: str = None):
        """Set or show the cooldown for emergency squawk alerts.
        
        Default cooldown is 5 minutes.
        Use without a value to check current setting.
        Accepts minutes (e.g. 5, 5m) or seconds (e.g. 30s)
        
        Examples:
            [p]aircraft alertcooldown 10m  - Set cooldown to 10 minutes
            [p]aircraft alertcooldown 30s  - Set cooldown to 30 seconds
            [p]aircraft alertcooldown      - Show current cooldown
        """
        await self.admin_commands.set_alert_cooldown(ctx, duration)

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

    @commands.is_owner()
    @aircraft_group.command(name='debugapi')
    async def aircraft_debugapi(self, ctx):
        """Debug API key and connection issues (DM only)."""
        await self.admin_commands.debug_api(ctx)

    @commands.is_owner()
    @aircraft_group.command(name='setapimode')
    async def aircraft_set_api_mode(self, ctx, mode: str):
        """Set which API to use globally: 'primary' or 'fallback'. (owner only)"""
        mode = mode.lower()
        if mode not in ("primary", "fallback"):
            await ctx.send("❌ Invalid mode. Use 'primary' or 'fallback'.")
            return
        await self.config.api_mode.set(mode)
        await ctx.send(f"✅ API mode set to **{mode}**.")
    
    # Custom Alerts Commands
    @commands.guild_only()
    @aircraft_group.command(name='addalert')
    async def aircraft_add_alert(self, ctx, alert_type: str, value: str, cooldown: int = 5, channel: discord.TextChannel = None):
        """Add a custom alert for specific aircraft or squawks.
        
        Alert types: icao, callsign, squawk, type, reg
        Cooldown: 1-1440 minutes (default: 5)
        Channel: Optional channel to send alerts to (default: uses alert channel)
        """
        await self.admin_commands.add_custom_alert(ctx, alert_type, value, cooldown, channel)
    
    @commands.guild_only()
    @aircraft_group.command(name='removealert')
    async def aircraft_remove_alert(self, ctx, alert_id: str):
        """Remove a custom alert by its ID."""
        await self.admin_commands.remove_custom_alert(ctx, alert_id)
    
    @commands.guild_only()
    @aircraft_group.command(name='listalerts')
    async def aircraft_list_alerts(self, ctx):
        """List all custom alerts for this server."""
        await self.admin_commands.list_custom_alerts(ctx)
    
    @commands.guild_only()
    @aircraft_group.command(name='clearalerts')
    async def aircraft_clear_alerts(self, ctx):
        """Clear all custom alerts for this server."""
        await self.admin_commands.clear_custom_alerts(ctx)

    @commands.guild_only()
    @commands.is_owner()
    @aircraft_group.command(name='forcealert', aliases=['forcecustomalert'])
    async def aircraft_force_alert(self, ctx, alert_id: str):
        """Force trigger a configured custom alert immediately by its ID (owner only)."""
        await self.admin_commands.force_custom_alert(ctx, alert_id)

    @commands.is_owner()
    @aircraft_group.command(name='apimode')
    async def aircraft_show_api_mode(self, ctx):
        """Show the current global API mode. (owner only)"""
        mode = await self.config.api_mode()
        await ctx.send(f"🌐 Current API mode: **{mode}**")

    @commands.is_owner()
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

    @commands.is_owner()
    @aircraft_group.command(name='debugtoggle')
    async def aircraft_debugtoggle(self, ctx, state: str = None):
        """Enable or disable aircraft debug output: *aircraft debugtoggle <on|off>"""
        if state is None or state.lower() not in ("on", "off"):
            await ctx.send("Usage: `*aircraft debugtoggle <on|off>`")
            return
        enabled = state.lower() == "on"
        await self.aircraft_commands.set_debug(ctx, enabled)

    @commands.is_owner()
    @aircraft_group.command(name="setapikey")
    async def aircraft_setapikey(self, ctx, api_key: str):
        """Set the airplanes.live API key."""
        await self.admin_commands.set_api_key(ctx, api_key)

    @commands.is_owner()
    @aircraft_group.command(name="apikey")
    async def aircraft_apikey(self, ctx):
        """Show the current airplanes.live API key (partially masked)."""
        await self.admin_commands.check_api_key(ctx)

    @commands.is_owner()
    @aircraft_group.command(name="clearapikey")
    async def aircraft_clearapikey(self, ctx):
        """Clear the airplanes.live API key."""
        await self.admin_commands.clear_api_key(ctx)

    # Airport commands
    @commands.guild_only()
    @commands.group(name='airport', help='Command center for airport related commands', invoke_without_command=True)
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

    @commands.is_owner()
    @airport_group.command(name="setowmkey")
    async def airport_setowmkey(self, ctx, api_key: str):
        """Set the OpenWeatherMap API key."""
        await self.admin_commands.set_owm_key(ctx, api_key)

    @commands.is_owner()
    @airport_group.command(name="owmkey")
    async def airport_owmkey(self, ctx):
        """Show the current OpenWeatherMap API key (partially masked)."""
        await self.admin_commands.check_owm_key(ctx)

    @commands.is_owner()
    @airport_group.command(name="clearowmkey")
    async def airport_clearowmkey(self, ctx):
        """Clear the OpenWeatherMap API key."""
        await self.admin_commands.clear_owm_key(ctx)

    @tasks.loop(minutes=2)
    async def check_emergency_squawks(self):
        """Background task to check for emergency squawks."""
        try:
            emergency_squawk_codes = ['7500', '7600', '7700']
            log.debug("Background task checking for emergency squawks...")
            for squawk_code in emergency_squawk_codes:
                # Use new REST API endpoint for squawk filter - must combine with base query
                url = f"{await self.api.get_api_url()}/?all_with_pos&filter_squawk={squawk_code}"
                response = await self.api.make_request(url)  # No ctx for background task
                aircraft_count = len(response.get('aircraft', [])) if response else 0
                log.debug(f"Checked {squawk_code}: Found {aircraft_count} aircraft")
                if response and 'aircraft' in response:
                    for aircraft_info in response['aircraft']:
                        # Ignore aircraft with the hex 00000000
                        if aircraft_info.get('hex') == '00000000':
                            continue
                        guilds = self.bot.guilds
                        for guild in guilds:
                            # In non-command contexts set locales explicitly
                            await set_contextual_locales_from_guild(self.bot, guild)
                            guild_config = self.config.guild(guild)
                            alert_channel_id = await guild_config.alert_channel()
                            if alert_channel_id:
                                icao_hex = aircraft_info.get('hex')
                                if not icao_hex:
                                    continue
                                
                                cooldown_minutes = await guild_config.emergency_cooldown()
                                alert_key = f"{icao_hex}-{squawk_code}"
                                now = datetime.datetime.now(datetime.timezone.utc)
                                
                                last_alerts = await guild_config.last_alerts()
                                last_alert_timestamp = last_alerts.get(alert_key)
                                
                                if last_alert_timestamp:
                                    last_alert_time = datetime.datetime.fromtimestamp(last_alert_timestamp, tz=datetime.timezone.utc)
                                    time_since_last = (now - last_alert_time).total_seconds()
                                    if time_since_last < cooldown_minutes * 60:
                                        log.debug(f"Cooldown active for {icao_hex} ({squawk_code}) - {time_since_last:.1f}s since last alert (cooldown: {cooldown_minutes}m)")
                                        continue  # Cooldown active, skip.
                                
                                alert_channel = self.bot.get_channel(alert_channel_id)
                                if alert_channel:
                                    # Update timestamp before sending, to be safe
                                    last_alerts = await guild_config.last_alerts()
                                    last_alerts[alert_key] = now.timestamp()
                                    # Clean up old entries
                                    keys_to_delete = [
                                        k for k, ts in last_alerts.items()
                                        if (now.timestamp() - ts) > (cooldown_minutes * 60)
                                    ]
                                    for k in keys_to_delete:
                                        if k != alert_key:
                                            del last_alerts[k]
                                    await guild_config.last_alerts.set(last_alerts)

                                    # Get the alert role
                                    alert_role_id = await guild_config.alert_role()
                                    alert_role_mention = f"<@&{alert_role_id}>" if alert_role_id else ""
                                    
                                    # Prepare message data for pre-send hooks
                                    message_data = {
                                        'content': alert_role_mention if alert_role_mention else None,
                                        'embed': None,
                                        'view': None,
                                    }
                                    # Compose the embed and view as before
                                    aircraft_data = aircraft_info
                                    image_url, photographer = await self.helpers.get_photo_by_aircraft_data(aircraft_data)
                                    embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
                                    
                                    # Create buttons for emergency alerts
                                    view = discord.ui.View()
                                    icao = aircraft_data.get('hex', '').upper()
                                    link = f"https://globe.airplanes.live/?icao={icao}"
                                    view.add_item(discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=link, style=discord.ButtonStyle.link))

                                    # Social media sharing buttons
                                    import urllib.parse
                                    ground_speed_knots = aircraft_data.get('gs', aircraft_data.get('ground_speed', 'N/A'))
                                    ground_speed_mph = 'unknown'
                                    if ground_speed_knots != 'N/A' and ground_speed_knots is not None:
                                        try:
                                            ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
                                        except Exception:
                                            ground_speed_mph = 'unknown'
                                    
                                    lat = aircraft_data.get('lat', 'N/A')
                                    lon = aircraft_data.get('lon', 'N/A')
                                    if lat != 'N/A' and lat is not None:
                                        try:
                                            lat_formatted = round(float(lat), 2)
                                            lat_dir = "N" if lat_formatted >= 0 else "S"
                                            lat = f"{abs(lat_formatted)}{lat_dir}"
                                        except Exception:
                                            pass
                                    if lon != 'N/A' and lon is not None:
                                        try:
                                            lon_formatted = round(float(lon), 2)
                                            lon_dir = "E" if lon_formatted >= 0 else "W"
                                            lon = f"{abs(lon_formatted)}{lon_dir}"
                                        except Exception:
                                            pass
                                    
                                    if squawk_code in ['7500', '7600', '7700']:
                                        tweet_text = f"Spotted an aircraft declaring an emergency! #Squawk #{squawk_code}, flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. #SkySearch #Emergency\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
                                    else:
                                        tweet_text = f"Tracking flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph using #SkySearch\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
                                    
                                    tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote_plus(tweet_text)}"
                                    view.add_item(discord.ui.Button(label="Post on X", emoji="📣", url=tweet_url, style=discord.ButtonStyle.link))
                                    
                                    whatsapp_text = f"Check out this aircraft! Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. Track live @ https://globe.airplanes.live/?icao={icao} #SkySearch"
                                    whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote_plus(whatsapp_text)}"
                                    view.add_item(discord.ui.Button(label="Send on WhatsApp", emoji="📱", url=whatsapp_url, style=discord.ButtonStyle.link))
                                    
                                    message_data['embed'] = embed
                                    message_data['view'] = view

                                    # Let other cogs know about the alert first
                                    log.error(f"DEBUG: Calling callbacks for {icao_hex} ({squawk_code}) in {guild.name}")
                                    await self.squawk_api.call_callbacks(guild, aircraft_info, squawk_code)
                                    log.error(f"DEBUG: Finished callbacks for {icao_hex}")

                                    # Let other cogs modify the message before sending
                                    original_view = message_data.get('view')
                                    message_data = await self.squawk_api.run_pre_send(guild, aircraft_info, squawk_code, message_data)
                                    
                                    # Ensure buttons are preserved if no other cog modified the view
                                    if message_data.get('view') is None and original_view is not None:
                                        log.warning(f"Pre-send callback removed view for {icao_hex}, restoring buttons")
                                        message_data['view'] = original_view

                                    # Send the message using the possibly modified data
                                    sent_message = await alert_channel.send(
                                        content=message_data.get('content'),
                                        embed=message_data.get('embed'),
                                        view=message_data.get('view')
                                    )

                                    # Let other cogs react after the message is sent
                                    await self.squawk_api.run_post_send(guild, aircraft_info, squawk_code, sent_message)
                                    
                                    # Check if aircraft has landed
                                    if aircraft_info.get('altitude') is not None and aircraft_info.get('altitude') < 25:
                                        embed = discord.Embed(title=_("Aircraft landed"), description=_("Aircraft {hex} has landed while squawking {squawk}.").format(hex=aircraft_info.get('hex'), squawk=squawk_code), color=0x00ff00)
                                        await alert_channel.send(embed=embed)
                
                # Check custom alerts against the full aircraft feed (not just emergency squawks)
                try:
                    all_url = f"{await self.api.get_api_url()}/?all_with_pos"
                    all_response = await self.api.make_request(all_url)
                    # Support both primary ('aircraft') and fallback ('ac') response formats
                    aircraft_list = []
                    if all_response:
                        if 'aircraft' in all_response:
                            aircraft_list = all_response['aircraft']
                        elif 'ac' in all_response and isinstance(all_response['ac'], list):
                            aircraft_list = all_response['ac']
                    if aircraft_list:
                        for aircraft_info in aircraft_list:
                            # Ignore aircraft with the hex 00000000
                            if aircraft_info.get('hex') == '00000000':
                                continue
                            await self.check_custom_alerts(aircraft_info)
                except Exception as e:
                    log.error(f"Error checking custom alerts feed: {e}", exc_info=True)

                # Removed the "No alert channel set" message - this is normal behavior
                await asyncio.sleep(2)
        except Exception as e:
            log.error(f"Error checking emergency squawks: {e}", exc_info=True)

    @check_emergency_squawks.before_loop
    async def before_check_emergency_squawks(self):
        """Wait for bot to be ready before starting the task."""
        await self.bot.wait_until_ready()
    
    async def check_custom_alerts(self, aircraft_info):
        """Check if aircraft matches any custom alerts for all guilds."""
        try:
            guilds = self.bot.guilds
            for guild in guilds:
                await set_contextual_locales_from_guild(self.bot, guild)
                guild_config = self.config.guild(guild)
                alert_channel_id = await guild_config.alert_channel()
                # Default alert channel may be unset; some alerts might target a custom channel.
                custom_alerts = await guild_config.custom_alerts()
                if not custom_alerts:
                    continue
                
                alert_channel = self.bot.get_channel(alert_channel_id) if alert_channel_id else None
                
                # Check each custom alert
                for alert_id, alert_data in custom_alerts.items():
                    if await self._check_aircraft_matches_alert(aircraft_info, alert_data):
                        if await self._is_alert_cooldown_active(guild_config, alert_id, alert_data):
                            continue
                        
                        # Determine if we have a destination channel: use custom channel if set, else default
                        destination_channel = alert_channel
                        custom_channel_id = alert_data.get('custom_channel')
                        if custom_channel_id:
                            custom_channel = self.bot.get_channel(custom_channel_id)
                            if custom_channel:
                                destination_channel = custom_channel
                        
                        if destination_channel is None:
                            log.warning(f"No alert channel configured for guild {guild.name} and no valid custom channel for alert {alert_id}; skipping send")
                            continue
                        
                        # Send custom alert
                        await self._send_custom_alert(destination_channel, guild_config, aircraft_info, alert_data, alert_id)
                        
                        # Update last triggered timestamp
                        custom_alerts[alert_id]['last_triggered'] = datetime.datetime.utcnow().isoformat()
                        await guild_config.custom_alerts.set(custom_alerts)
                        
        except Exception as e:
            log.error(f"Error checking custom alerts: {e}", exc_info=True)
    
    async def _check_aircraft_matches_alert(self, aircraft_info, alert_data):
        """Check if aircraft matches the alert criteria."""
        alert_type = alert_data['type']
        alert_value = alert_data['value'].lower()
        
        if alert_type == 'icao':
            return aircraft_info.get('hex', '').lower() == alert_value
        elif alert_type == 'callsign':
            return aircraft_info.get('flight', '').lower() == alert_value
        elif alert_type == 'squawk':
            return aircraft_info.get('squawk', '') == alert_value
        elif alert_type == 'type':
            return aircraft_info.get('t', '').lower() == alert_value
        elif alert_type == 'reg':
            return aircraft_info.get('r', '').lower() == alert_value
        
        return False
    
    async def _is_alert_cooldown_active(self, guild_config, alert_id, alert_data):
        """Check if alert is in cooldown period."""
        cooldown_minutes = alert_data['cooldown']
        last_triggered = alert_data.get('last_triggered')
        
        if not last_triggered:
            return False
        
        last_triggered_time = datetime.datetime.fromisoformat(last_triggered)
        now = datetime.datetime.utcnow()
        time_since_last = (now - last_triggered_time).total_seconds()
        
        return time_since_last < (cooldown_minutes * 60)
    
    async def _send_custom_alert(self, alert_channel, guild_config, aircraft_info, alert_data, alert_id):
        """Send a custom alert message."""
        try:
            # Use custom channel if specified, otherwise use the default alert channel
            custom_channel_id = alert_data.get('custom_channel')
            if custom_channel_id:
                custom_channel = self.bot.get_channel(custom_channel_id)
                if custom_channel:
                    alert_channel = custom_channel
                else:
                    log.warning(f"Custom channel {custom_channel_id} not found for alert {alert_id}, using default channel")
            
            # Get the alert role
            alert_role_id = await guild_config.alert_role()
            alert_role_mention = f"<@&{alert_role_id}>" if alert_role_id else ""
            
            # Create embed
            aircraft_data = aircraft_info
            image_url, photographer = await self.helpers.get_photo_by_aircraft_data(aircraft_data)
            embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
            
            # Add custom alert header
            embed.title = f"🔔 Custom Alert: {alert_data['type'].upper()} '{alert_data['value']}'"
            embed.color = 0xffaa00  # Orange color for custom alerts
            
            # Create view with buttons
            view = discord.ui.View()
            icao = aircraft_data.get('hex', '').upper()
            link = f"https://globe.airplanes.live/?icao={icao}"
            view.add_item(discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=link, style=discord.ButtonStyle.link))
            
            # Add social media sharing buttons
            import urllib.parse
            ground_speed_knots = aircraft_data.get('gs', aircraft_data.get('ground_speed', 'N/A'))
            ground_speed_mph = 'unknown'
            if ground_speed_knots != 'N/A' and ground_speed_knots is not None:
                try:
                    ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
                except Exception:
                    ground_speed_mph = 'unknown'
            
            lat = aircraft_data.get('lat', 'N/A')
            lon = aircraft_data.get('lon', 'N/A')
            if lat != 'N/A' and lat is not None:
                try:
                    lat_formatted = round(float(lat), 2)
                    lat_dir = "N" if lat_formatted >= 0 else "S"
                    lat = f"{abs(lat_formatted)}{lat_dir}"
                except Exception:
                    pass
            if lon != 'N/A' and lon is not None:
                try:
                    lon_formatted = round(float(lon), 2)
                    lon_dir = "E" if lon_formatted >= 0 else "W"
                    lon = f"{abs(lon_formatted)}{lon_dir}"
                except Exception:
                    pass
            
            tweet_text = f"Custom alert triggered! {alert_data['type'].upper()} '{alert_data['value']}' spotted - Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. #SkySearch #CustomAlert\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
            tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote_plus(tweet_text)}"
            view.add_item(discord.ui.Button(label="Post on X", emoji="📣", url=tweet_url, style=discord.ButtonStyle.link))
            
            whatsapp_text = f"Custom alert! {alert_data['type'].upper()} '{alert_data['value']}' spotted - Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. Track live @ https://globe.airplanes.live/?icao={icao} #SkySearch"
            whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote_plus(whatsapp_text)}"
            view.add_item(discord.ui.Button(label="Send on WhatsApp", emoji="📱", url=whatsapp_url, style=discord.ButtonStyle.link))
            
            # Send the alert
            await alert_channel.send(
                content=alert_role_mention if alert_role_mention else None,
                embed=embed,
                view=view
            )
            
            log.info(f"Sent custom alert for {alert_id} in {alert_channel.guild.name}")
            
        except Exception as e:
            log.error(f"Error sending custom alert {alert_id}: {e}", exc_info=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle automatic ICAO lookup."""
        if message.author == self.bot.user:
            return

        if message.guild is None:
            return

        # Ensure locales for non-command listener
        await set_contextual_locales_from_guild(self.bot, message.guild)

        auto_icao = await self.config.guild(message.guild).auto_icao()
        if not auto_icao:
            return

        content = message.content
        icao_pattern = re.compile(r'^[a-fA-F0-9]{6}$')

        if icao_pattern.match(content):
            ctx = await self.bot.get_context(message)
            await self.aircraft_commands.aircraft_by_icao(ctx, content)
        
    @commands.is_owner()
    @aircraft_group.command(name="simulateemergency")
    async def simulate_emergency_alert(self, ctx, hex_code: str, squawk_code: str = "7700", callsign: str = "TEST123"):
        """Simulate a new emergency alert for testing callbacks (owner only).
        
        Usage: *aircraft simulateemergency <hex_code> [squawk_code] [callsign]
        Examples:
        - *aircraft simulateemergency ABC123
        - *aircraft simulateemergency DEF456 7600 UNITED789
        """
        # Validate squawk code
        emergency_squawk_codes = ['7500', '7600', '7700']
        if squawk_code not in emergency_squawk_codes:
            await ctx.send(_("❌ Invalid squawk code. Valid codes are: {codes}").format(codes=', '.join(emergency_squawk_codes)))
            return
            
        # Validate hex code format
        if not hex_code or len(hex_code) != 6 or not all(c in '0123456789ABCDEFabcdef' for c in hex_code):
            await ctx.send(_("❌ Invalid hex code. Must be 6 hexadecimal characters (e.g., ABC123)"))
            return
            
        hex_code = hex_code.upper()
        
        await ctx.send(_("🧪 Simulating emergency alert: {hex} squawking {squawk}...").format(hex=hex_code, squawk=squawk_code))
        
        # Create realistic fake aircraft data
        fake_aircraft = {
            'hex': hex_code,
            'flight': callsign,
            'lat': 40.7128 + (hash(hex_code) % 1000) / 10000,  # Vary position based on hex
            'lon': -74.0060 + (hash(hex_code) % 1000) / 10000,
            'altitude': 35000 + (hash(hex_code) % 5000),
            'ground_speed': 450 + (hash(hex_code) % 100),
            'squawk': squawk_code,
            'alt_baro': 35000 + (hash(hex_code) % 5000),
            'track': hash(hex_code) % 360
        }
        
        # Simulate the exact same logic as the background task
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        alert_channel_id = await guild_config.alert_channel()
        
        if not alert_channel_id:
            await ctx.send(_("❌ No alert channel configured. Use `*aircraft alertchannel #channel` first."))
            return
            
        # Check cooldown (same logic as background task)
        cooldown_minutes = await guild_config.emergency_cooldown()
        alert_key = f"{hex_code}-{squawk_code}"
        now = datetime.datetime.now(datetime.timezone.utc)
        
        last_alerts = await guild_config.last_alerts()
        last_alert_timestamp = last_alerts.get(alert_key)
        
        if last_alert_timestamp:
            last_alert_time = datetime.datetime.fromtimestamp(last_alert_timestamp, tz=datetime.timezone.utc)
            time_since_last = (now - last_alert_time).total_seconds()
            if time_since_last < cooldown_minutes * 60:
                await ctx.send(f"⏰ Cooldown active for {hex_code} ({squawk_code}): {time_since_last:.1f}s since last alert (cooldown: {cooldown_minutes}m)")
                return
        
        alert_channel = self.bot.get_channel(alert_channel_id)
        if not alert_channel:
            await ctx.send(_("❌ Alert channel {channel_id} not found").format(channel_id=alert_channel_id))
            return
            
        # Update timestamp (same as background task)
        last_alerts = await guild_config.last_alerts()
        last_alerts[alert_key] = now.timestamp()
        
        # Clean up old entries
        keys_to_delete = [
            k for k, ts in last_alerts.items()
            if (now.timestamp() - ts) > (cooldown_minutes * 60)
        ]
        for k in keys_to_delete:
            if k != alert_key:
                del last_alerts[k]
        await guild_config.last_alerts.set(last_alerts)

        # Get the alert role
        alert_role_id = await guild_config.alert_role()
        alert_role_mention = f"<@&{alert_role_id}>" if alert_role_id else ""
        
        # Prepare message data for pre-send hooks
        message_data = {
            'content': alert_role_mention if alert_role_mention else None,
            'embed': None,
            'view': None,
        }
        
        # Create embed and buttons (same as real background task)
        aircraft_data = fake_aircraft
        image_url, photographer = await self.helpers.get_photo_by_aircraft_data(aircraft_data)
        embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
        
        # Create buttons (same as real emergency alerts)
        view = discord.ui.View()
        icao = aircraft_data.get('hex', '').upper()
        link = f"https://globe.airplanes.live/?icao={icao}"
        view.add_item(discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=link, style=discord.ButtonStyle.link))

        # Social media sharing (same as real alerts)
        import urllib.parse
        ground_speed_knots = aircraft_data.get('gs', aircraft_data.get('ground_speed', 'N/A'))
        ground_speed_mph = 'unknown'
        if ground_speed_knots != 'N/A' and ground_speed_knots is not None:
            try:
                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
            except Exception:
                ground_speed_mph = 'unknown'
        
        lat = aircraft_data.get('lat', 'N/A')
        lon = aircraft_data.get('lon', 'N/A')
        if lat != 'N/A' and lat is not None:
            try:
                lat_formatted = round(float(lat), 2)
                lat_dir = "N" if lat_formatted >= 0 else "S"
                lat = f"{abs(lat_formatted)}{lat_dir}"
            except Exception:
                pass
        if lon != 'N/A' and lon is not None:
            try:
                lon_formatted = round(float(lon), 2)
                lon_dir = "E" if lon_formatted >= 0 else "W"
                lon = f"{abs(lon_formatted)}{lon_dir}"
            except Exception:
                pass
        
        if squawk_code in ['7500', '7600', '7700']:
            tweet_text = f"Spotted an aircraft declaring an emergency! #Squawk #{squawk_code}, flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. #SkySearch #Emergency\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
        else:
            tweet_text = f"Tracking flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph using #SkySearch\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
        
        tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote_plus(tweet_text)}"
        view.add_item(discord.ui.Button(label="Post on X", emoji="📣", url=tweet_url, style=discord.ButtonStyle.link))
        
        whatsapp_text = f"Check out this aircraft! Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. Track live @ https://globe.airplanes.live/?icao={icao} #SkySearch"
        whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote_plus(whatsapp_text)}"
        view.add_item(discord.ui.Button(label="Send on WhatsApp", emoji="📱", url=whatsapp_url, style=discord.ButtonStyle.link))
        
        message_data['embed'] = embed
        message_data['view'] = view

        log.info(f"SIMULATE: About to call squawk API callbacks for {hex_code} with squawk {squawk_code} in guild {guild.name}")
        log.info(f"SIMULATE: Number of registered callbacks: {len(self.squawk_api._callbacks)}")

        # Let other cogs know about the alert first (THIS IS THE KEY PART)
        await self.squawk_api.call_callbacks(guild, fake_aircraft, squawk_code)

        log.info(f"SIMULATE: Finished calling squawk API callbacks for {hex_code}")

        # Let other cogs modify the message before sending
        original_view = message_data.get('view')
        message_data = await self.squawk_api.run_pre_send(guild, fake_aircraft, squawk_code, message_data)
        
        # Ensure buttons are preserved if no other cog modified the view
        if message_data.get('view') is None and original_view is not None:
            log.warning(f"Pre-send callback removed view for {hex_code}, restoring buttons")
            message_data['view'] = original_view

        # Send the message using the possibly modified data
        sent_message = await alert_channel.send(
            content=message_data.get('content'),
            embed=message_data.get('embed'),
            view=message_data.get('view')
        )

        # Let other cogs react after the message is sent
        await self.squawk_api.run_post_send(guild, fake_aircraft, squawk_code, sent_message)
        
        await ctx.send(_("✅ Simulated emergency alert sent! Check #{channel} and console logs.").format(channel=alert_channel.name))

    @commands.is_owner()
    @aircraft_group.command(name="clearalertcooldowns")
    async def clear_alert_cooldowns(self, ctx):
        """Clear all alert cooldowns for this guild (owner only)."""
        guild_config = self.config.guild(ctx.guild)
        await guild_config.last_alerts.set({})
        await ctx.send(_("✅ All alert cooldowns cleared for this guild."))
        
        
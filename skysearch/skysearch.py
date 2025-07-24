"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

import discord
import asyncio
import re
import datetime
import aiohttp
from redbot.core import commands, Config
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



class Skysearch(commands.Cog, DashboardIntegration):
    """SkySearch - Aircraft tracking and information cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self._skysearch_cog = self  # For dashboard integration access
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.config.register_global(airplanesliveapi=None)  # API key for airplanes.live
        self.config.register_global(openweathermap_api=None)  # OWM API key
        self.config.register_global(api_mode="primary")  # API mode: 'primary' or 'fallback (going to remove this when airplanes.live removes the public api because of companies abusing it...when that happens you'll need an api key for it)'
        self.config.register_guild(alert_channel=None, alert_role=None, auto_icao=False, auto_delete_not_found=True, emergency_cooldown=5, last_alerts={})
        
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

    def register_squawk_alert_callback(self, callback):
        """
        Register a callback to be called when a squawk alert is triggered.
        The callback should be a coroutine function accepting (guild, aircraft_info, squawk_code).
        """
        self.squawk_api.register_callback(callback)

    async def cog_unload(self):
        """Clean up when the cog is unloaded."""
        await self.api.close()

    @commands.guild_only()
    @commands.group(name='skysearch', help='Core menu for the cog', invoke_without_command=True)
    async def skysearch(self, ctx):
        """SkySearch command group"""
        embed = discord.Embed(title="Thanks for using SkySearch", description="SkySearch is a powerful, easy-to-use OSINT tool for tracking aircraft.", color=0xfffffe)
        embed.add_field(name="aircraft", value="Use `aircraft` to show available commands to fetch information about live aircraft and configure emergency squawk alerts.", inline=False)
        embed.add_field(name="airport", value="Use `airport` to show available commands to fetch information and imagery of airports around the world.", inline=False)
        await ctx.send(embed=embed)
    
    @commands.guild_only()
    @skysearch.command(name='stats', help='Get statistics about SkySearch and the data used here')
    async def stats(self, ctx):
        """Get SkySearch statistics."""
        data = await self.api.get_stats()

        embed = discord.Embed(title="SkySearch Statistics", description="Consolidated statistics and data sources for SkySearch.", color=0xfffffe)
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

    # Aircraft commands
    @commands.guild_only()
    @commands.group(name='aircraft', help='Command center for aircraft related commands', invoke_without_command=True)
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
            for squawk_code in emergency_squawk_codes:
                # Use new REST API endpoint for squawk filter - must combine with base query
                url = f"{await self.api.get_api_url()}/?all_with_pos&filter_squawk={squawk_code}"
                response = await self.api.make_request(url)  # No ctx for background task
                if response and 'aircraft' in response:
                    for aircraft_info in response['aircraft']:
                        # Ignore aircraft with the hex 00000000
                        if aircraft_info.get('hex') == '00000000':
                            continue
                        guilds = self.bot.guilds
                        for guild in guilds:
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
                                    if (now - last_alert_time).total_seconds() < cooldown_minutes * 60:
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
                                    embed, view = None, None
                                    # If you have a custom embed/view creation, do it here:
                                    # (Assume send_aircraft_info returns embed/view or you can call a helper)
                                    # For now, let's use the helpers directly:
                                    aircraft_data = aircraft_info
                                    image_url, photographer = await self.helpers.get_photo_by_hex(aircraft_data.get('hex', None))
                                    embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
                                    view = None
                                    # If you use a view (buttons), create it here as before
                                    # ... (existing view logic if any) ...
                                    message_data['embed'] = embed
                                    message_data['view'] = view

                                    # Let other cogs know about the alert first
                                    await self.squawk_api.call_callbacks(guild, aircraft_info, squawk_code)

                                    # Let other cogs modify the message before sending
                                    message_data = await self.squawk_api.run_pre_send(guild, aircraft_info, squawk_code, message_data)

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
                                        embed = discord.Embed(title="Aircraft landed", description=f"Aircraft {aircraft_info.get('hex')} has landed while squawking {squawk_code}.", color=0x00ff00)
                                        await alert_channel.send(embed=embed)
                                else:
                                    # Only log if channel was set but not found (actual error)
                                    print(f"Warning: Alert channel {alert_channel_id} not found for guild {guild.name} - channel may have been deleted")
                            # Removed the "No alert channel set" message - this is normal behavior
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Error checking emergency squawks: {e}")

    @check_emergency_squawks.before_loop
    async def before_check_emergency_squawks(self):
        """Wait for bot to be ready before starting the task."""
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
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
        
        
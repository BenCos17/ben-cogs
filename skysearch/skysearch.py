"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

import discord
import asyncio
import re
import datetime
import aiohttp
from discord.ext import tasks, commands
from redbot.core import commands, Config

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


class Skysearch(commands.Cog):
    """SkySearch - Aircraft tracking and information cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.config.register_global(airplanesliveapi=None)  # API key for airplanes.live
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
    @commands.guild_only()
    @commands.group(name='aircraft', help='Command center for aircraft related commands')
    async def aircraft_group(self, ctx):
        """Command center for aircraft related commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Aircraft Commands", description="Available aircraft-related commands:", color=0xfffffe)
            embed.add_field(name="Search Commands", value="`icao` `callsign` `reg` `type` `squawk` `radius` `closest`", inline=False)
            embed.add_field(name="Special Aircraft", value="`military` `ladd` `pia`", inline=False)
            embed.add_field(name="Export", value="`export` - Export aircraft data to CSV, PDF, TXT, or HTML", inline=False)
            embed.add_field(name="Configuration", value="`alertchannel` `alertrole` `autoicao` `autodelete` `showalertchannel`", inline=False)
            embed.add_field(name="Other", value="`scroll` - Scroll through available planes", inline=False)
            await ctx.send(embed=embed)

    # Airport commands
    @commands.guild_only()
    @commands.group(name='airport', help='Command center for airport related commands')
    async def airport_group(self, ctx):
        """Command center for airport related commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Airport Commands", description="Available airport-related commands:", color=0xfffffe)
            embed.add_field(name="Information", value="`info` - Get airport information by ICAO/IATA code", inline=False)
            embed.add_field(name="Details", value="`runway` - Get runway information\n`navaid` - Get navigational aids\n`forecast` - Get weather forecast", inline=False)
            await ctx.send(embed=embed)

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

    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        try:
            self.check_emergency_squawks.cancel()
        except Exception as e:
            print(f"Error unloading cog: {e}")

    # Delegate commands to appropriate modules
    def __getattr__(self, name):
        """Delegate attribute access to command modules."""
        # Check if the attribute exists in any of the command modules
        for module in [self.aircraft_commands, self.airport_commands, self.admin_commands]:
            if hasattr(module, name):
                return getattr(module, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        
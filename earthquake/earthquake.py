import discord
from redbot.core import commands, Config
from discord.ext import tasks
import aiohttp
import json
import datetime
import logging

class Earthquake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stop_messages = False
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {
            "alert_channel_id": None,
            "min_magnitude": 5,
            "announced_earthquake_ids": []  # Track announced earthquake IDs per guild
        }
        self.config.register_guild(**default_guild)
        logging.basicConfig(level=logging.INFO)
        self.check_earthquakes.start()

    @commands.command(name='setalertchannel', help='Set the channel for earthquake alerts. Usage: !setalertchannel <channel>')
    async def set_alert_channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).alert_channel_id.set(channel.id)  # Set to the specified channel
        logging.info(f"Alert channel set to {channel.id} ({channel.name}) for guild {ctx.guild.id}.")  # Added logging
        await ctx.send(f"Alert channel set to {channel.name}.")

    @commands.command(name='setminmagnitude', help='Set the minimum magnitude for alerts')
    async def set_min_magnitude(self, ctx, magnitude: float):
        await self.config.guild(ctx.guild).min_magnitude.set(magnitude)
        await ctx.send(f"Minimum magnitude for alerts set to {magnitude}.")

    @tasks.loop(minutes=10)
    async def check_earthquakes(self):
        guilds = self.bot.guilds
        for guild in guilds:
            alert_channel_id = await self.config.guild(guild).alert_channel_id()
            min_magnitude = await self.config.guild(guild).min_magnitude()
            if alert_channel_id is None:  # Check if alert channel is not set
                continue  # Do not check if alert channel is not set
            if self.stop_messages:  # Check if messages should be stopped
                continue  # Do not check if messages are stopped

            url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
            params = {
                'format': 'geojson',
                'orderby': 'time',
                'minmagnitude': min_magnitude  # Use the configured minimum magnitude
            }
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, params=params) as response:
                        response.raise_for_status()
                        data = await response.json()
                        if data['metadata']['count'] > 0:
                            # Get announced earthquake IDs from config
                            announced_ids = set(await self.config.guild(guild).announced_earthquake_ids())
                            new_announced_ids = set(announced_ids)
                            for feature in data['features']:
                                eq_id = feature.get('id')
                                if eq_id in announced_ids:
                                    continue  # Already announced
                                if self.stop_messages:  # Check here before sending
                                    break
                                # Send alert for each new earthquake
                                await self.send_earthquake_embed(self.bot.get_channel(alert_channel_id), feature)
                                new_announced_ids.add(eq_id)
                            # Save updated announced IDs (keep only the most recent 100 to avoid bloat)
                            if new_announced_ids != announced_ids:
                                # Sort by most recent in data['features'] order
                                recent_ids = [f.get('id') for f in data['features'] if f.get('id') in new_announced_ids]
                                # Add any old IDs not in this batch
                                for old_id in announced_ids:
                                    if old_id not in recent_ids:
                                        recent_ids.append(old_id)
                                await self.config.guild(guild).announced_earthquake_ids.set(recent_ids[:100])
                except Exception as e:
                    logging.error(f"Error fetching earthquake data: {e}")

    @check_earthquakes.before_loop
    async def before_check_earthquakes(self):
        await self.bot.wait_until_ready()

    async def send_earthquake_embed(self, ctx, feature, webhook=None):
        utc_time = datetime.datetime.utcfromtimestamp(feature['properties']['time'] / 1000)
        embed = discord.Embed(title="Earthquake Alert", description=f"Location: {feature['properties']['place']}", color=0x00ff00, timestamp=utc_time)
        embed.add_field(name="Magnitude", value=feature['properties']['mag'], inline=False)
        embed.add_field(name="Time", value=discord.utils.format_dt(utc_time, style='F'), inline=False)
        embed.add_field(name="Depth", value=feature['geometry']['coordinates'][2], inline=False)
        embed.add_field(name="More Info", value=f"[USGS Info Page]({feature['properties']['url']})", inline=False)
        
        if webhook:
            await webhook.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.command(name='earthquake', help='Get the latest earthquake information. Use !earthquake <type> <params>. Type can be "rectangle" or "circle".')
    async def earthquake(self, ctx, search_type: str, *, params: str):
        if self.stop_messages:  # Check if messages should be stopped
            await ctx.send("Earthquake messages are currently stopped.")
            return

        url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
        params_dict = {
            'format': 'geojson',
            'orderby': 'time',
        }

        if search_type.lower() == "rectangle":
            try:
                # Expecting params in the format: "minlat,maxlat,minlon,maxlon"
                minlat, maxlat, minlon, maxlon = map(float, params.split(','))
                params_dict['minlatitude'] = minlat
                params_dict['maxlatitude'] = maxlat
                params_dict['minlongitude'] = minlon
                params_dict['maxlongitude'] = maxlon
            except ValueError:
                await ctx.send("Invalid parameters for rectangle. Use: minlat,maxlat,minlon,maxlon")
                return

        elif search_type.lower() == "circle":
            try:
                # Expecting params in the format: "latitude,longitude,maxradiuskm"
                latitude, longitude, maxradiuskm = map(float, params.split(','))
                params_dict['latitude'] = latitude
                params_dict['longitude'] = longitude
                params_dict['maxradiuskm'] = maxradiuskm
            except ValueError:
                await ctx.send("Invalid parameters for circle. Use: latitude,longitude,maxradiuskm")
                return

        else:
            await ctx.send("Invalid search type. Use 'rectangle' or 'circle'.")
            return

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params_dict) as response:
                    response.raise_for_status()  # Raise an error for bad responses
                    data = await response.json()
            except Exception as e:
                logging.error(f"Error fetching earthquake data: {e}")
                await ctx.send(f"Failed to fetch earthquake data: {str(e)}")
                return

        if data['metadata']['count'] > 0:
            try:
                avatar_bytes = await self.bot.user.avatar.read()
                webhook = await ctx.channel.create_webhook(name="Earthquake Alert Webhook", avatar=avatar_bytes)
                for feature in data['features']:
                    if self.stop_messages:
                        break
                    await self.send_earthquake_embed(ctx, feature, webhook)
                await webhook.delete()
            except discord.Forbidden:
                for feature in data['features']:
                    if self.stop_messages:
                        break
                    await self.send_earthquake_embed(ctx, feature)
        else:
            await ctx.send("No earthquakes found in the given parameters.")

    @commands.command(name='eqstop', help='Stop all earthquake messages and tasks')
    async def stop_messages(self, ctx):
        self.stop_messages = True  # Set the flag to stop messages
        self.check_earthquakes.stop()  # Stop the task loop
        await ctx.send("All earthquake messages and tasks have been stopped.")

    @commands.command(name='eqstart', help='Restart earthquake messages and tasks')
    async def start_messages(self, ctx):
        if self.check_earthquakes.is_running():  # Check if the task is already running
            await ctx.send("Earthquake messages are already running.")
            return
        self.stop_messages = False  # Reset the flag to allow messages
        self.check_earthquakes.start()  # Restart the task loop
        await ctx.send("Earthquake messages and tasks have been restarted.")

    @commands.command(name='testalert', help='Test the earthquake alert system')
    async def test_alert(self, ctx):
        alert_channel_id = await self.config.guild(ctx.guild).alert_channel_id()
        if alert_channel_id is None:
            await ctx.send("Alert channel is not set. Use `!setalertchannel` to set it.")
            return
        test_feature = {
            'properties': {
                'place': 'Test Location',
                'mag': 5.0,
                'time': datetime.datetime.now().timestamp() * 1000,
                'url': 'https://earthquake.usgs.gov/'
            },
            'geometry': {
                'coordinates': [0, 0, 10]
            }
        }
        await self.send_earthquake_embed(ctx, test_feature)

    @commands.command(name='forceupdate', help='Force an update for earthquake alerts')
    async def force_update(self, ctx):
        alert_channel_id = await self.config.guild(ctx.guild).alert_channel_id()
        if alert_channel_id is None:
            await ctx.send("Alert channel is not set. Use `!setalertchannel` to set it.")
            return
        await self.check_earthquakes()  # Manually trigger the check for earthquakes
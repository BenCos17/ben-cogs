import discord
from redbot.core import commands
from discord.ext import tasks
import aiohttp
import json
import datetime
import logging

class Earthquake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stop_messages = False
        self.alert_channel_id = None  # Store the alert channel ID
        self.min_magnitude = 5  # Default minimum magnitude
        logging.basicConfig(level=logging.INFO)
        self.check_earthquakes.start()

    @commands.command(name='setalertchannel', help='Set the channel for earthquake alerts')
    async def set_alert_channel(self, ctx):
        self.alert_channel_id = ctx.channel.id
        await ctx.send(f"Alert channel set to {ctx.channel.name}.")

    @commands.command(name='setminmagnitude', help='Set the minimum magnitude for alerts')
    async def set_min_magnitude(self, ctx, magnitude: float):
        self.min_magnitude = magnitude
        await ctx.send(f"Minimum magnitude for alerts set to {self.min_magnitude}.")

    @tasks.loop(minutes=10)
    async def check_earthquakes(self):
        if self.alert_channel_id is None:
            return  # Do not check if alert channel is not set

        url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
        params = {
            'format': 'geojson',
            'orderby': 'time',
            'minmagnitude': self.min_magnitude  # Use the configured minimum magnitude
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data['metadata']['count'] > 0:
                        for feature in data['features']:
                            if self.stop_messages:
                                break
                            # Send alert for each new earthquake
                            await self.send_earthquake_embed(self.bot.get_channel(self.alert_channel_id), feature)
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

    @commands.command(name='earthquake', help='Get the latest earthquake information')
    async def earthquake(self, ctx, *, search_query: str = None):
        url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
        params = {
            'format': 'geojson',
            'orderby': 'time',
        }
        
        # Set minmagnitude only if no search query is provided
        if search_query:
            params['query'] = search_query
        else:
            params['minmagnitude'] = self.min_magnitude  # Use configured min magnitude
            params['starttime'] = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            params['endtime'] = datetime.datetime.now().strftime('%Y-%m-%d')

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
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
            await ctx.send("No earthquakes found in the given time period or matching the search query.")

    @commands.command(name='eqstop', help='Stop the earthquake messages')
    async def stop_messages(self, ctx):
        self.stop_messages = True
        await ctx.send("Earthquake messages stopped.")

    @commands.command(name='testalert', help='Test the earthquake alert system')
    async def test_alert(self, ctx):
        if self.alert_channel_id is None:
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
        if self.alert_channel_id is None:
            await ctx.send("Alert channel is not set. Use `!setalertchannel` to set it.")
            return
        await self.check_earthquakes()  # Manually trigger the check for earthquakes
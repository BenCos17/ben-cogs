import discord
from redbot.core import commands
import aiohttp
import json
import datetime
import logging  # Added logging

class Earthquake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stop_messages = False
        logging.basicConfig(level=logging.INFO)  # Configure logging

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
            'minmagnitude': '5' if not search_query else None  # Set minmagnitude conditionally
        }
        if search_query:
            params['query'] = search_query
        else:
            params['starttime'] = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            params['endtime'] = datetime.datetime.now().strftime('%Y-%m-%d')

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()  # Raise an error for bad responses
                    data = await response.json()
            except Exception as e:
                logging.error(f"Error fetching earthquake data: {e}")
                await ctx.send("Failed to fetch earthquake data.")
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
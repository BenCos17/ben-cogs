import discord
from redbot.core import commands
import requests

class Airplaneslive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.airplanes.live/v2"

    @commands.command(name='aircraft_by_hex')
    async def aircraft_by_hex(self, ctx, hex_id):
        url = f"{self.api_url}/hex/{hex_id}"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='aircraft_by_callsign')
    async def aircraft_by_callsign(self, ctx, callsign):
        url = f"{self.api_url}/callsign/{callsign}"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='aircraft_by_reg')
    async def aircraft_by_reg(self, ctx, registration):
        url = f"{self.api_url}/reg/{registration}"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='aircraft_by_type')
    async def aircraft_by_type(self, ctx, aircraft_type):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='aircraft_by_squawk')
    async def aircraft_by_squawk(self, ctx, squawk_value):
        url = f"{self.api_url}/squawk/{squawk_value}"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='military_aircraft')
    async def military_aircraft(self, ctx):
        url = f"{self.api_url}/mil"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='ladd_aircraft')
    async def ladd_aircraft(self, ctx):
        url = f"{self.api_url}/ladd"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='pia_aircraft')
    async def pia_aircraft(self, ctx):
        url = f"{self.api_url}/pia"
        response = self._make_request(url)
        await ctx.send(response)

    @commands.command(name='aircraft_within_radius')
    async def aircraft_within_radius(self, ctx, lat, lon, radius):
        url = f"{self.api_url}/point/{lat}/{lon}/{radius}"
        response = self._make_request(url)
        await ctx.send(response)

    def _make_request(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error making request: {e}"

def setup(bot):
    bot.add_cog(AirplanesCog(bot))

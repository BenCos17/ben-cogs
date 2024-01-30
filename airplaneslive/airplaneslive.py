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
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='aircraft_by_callsign')
    async def aircraft_by_callsign(self, ctx, callsign):
        url = f"{self.api_url}/callsign/{callsign}"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='aircraft_by_reg')
    async def aircraft_by_reg(self, ctx, registration):
        url = f"{self.api_url}/reg/{registration}"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='aircraft_by_type')
    async def aircraft_by_type(self, ctx, aircraft_type):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='aircraft_by_squawk')
    async def aircraft_by_squawk(self, ctx, squawk_value):
        url = f"{self.api_url}/squawk/{squawk_value}"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='military_aircraft')
    async def military_aircraft(self, ctx):
        url = f"{self.api_url}/mil"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='ladd_aircraft')
    async def ladd_aircraft(self, ctx):
        url = f"{self.api_url}/ladd"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='pia_aircraft')
    async def pia_aircraft(self, ctx):
        url = f"{self.api_url}/pia"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    @commands.command(name='aircraft_within_radius')
    async def aircraft_within_radius(self, ctx, lat, lon, radius):
        url = f"{self.api_url}/point/{lat}/{lon}/{radius}"
        response = self._make_request(url)
        formatted_response = self._format_response(response)
        await ctx.send(formatted_response)

    def _make_request(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error making request: {e}"

    def _format_response(self, response):
        if 'ac' in response and response['ac']:
            aircraft_data = response['ac'][0]
            formatted_data = (
                f"**Flight:** {aircraft_data['flight'].strip()}\n"
                f"**Type:** {aircraft_data['desc']} ({aircraft_data['t']})\n"
                f"**Altitude:** {aircraft_data.get('alt_baro', 'N/A')} feet\n"
                f"**Ground Speed:** {aircraft_data.get('gs', 'N/A')} knots\n"
                f"**Heading:** {aircraft_data.get('true_heading', 'N/A')} degrees\n"
                f"**Latitude:** {aircraft_data.get('lat', 'N/A')}\n"
                f"**Longitude:** {aircraft_data.get('lon', 'N/A')}\n"
                f"**Squawk:** {aircraft_data.get('squawk', 'N/A')}\n"
                f"**Emergency:** {aircraft_data.get('emergency', 'N/A')}\n"
                f"**Operator:** {aircraft_data.get('ownOp', 'N/A')}\n"
                f"**Year:** {aircraft_data.get('year', 'N/A')}\n"
                f"**Category:** {aircraft_data.get('category', 'N/A')}\n"
                f"**Aircraft Type:** {aircraft_data.get('t', 'N/A')}\n"
                f"**Speed:** {aircraft_data.get('gs', 'N/A')} knots\n"
                f"**Altitude Rate:** {aircraft_data.get('baro_rate', 'N/A')} feet/minute\n"
                f"**Vertical Rate:** {aircraft_data.get('geom_rate', 'N/A')} feet/minute"
            )
            return formatted_data
        else:
            return "No aircraft found with the specified callsign."

def setup(bot):
    bot.add_cog(Airplaneslive(bot))

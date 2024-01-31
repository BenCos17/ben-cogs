import discord
from redbot.core import commands
import requests

class Airplaneslive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.airplanes.live/v2"
        self.max_requests_per_user = 10  # Set a default value; bot owner can change it

    @commands.command(name='aircraft_by_hex', help='Get information about an aircraft by its hexadecimal identifier.')
    async def aircraft_by_hex(self, ctx, hex_id):
        url = f"{self.api_url}/hex/{hex_id}"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @commands.command(name='aircraft_by_callsign', help='Get information about an aircraft by its callsign.')
    async def aircraft_by_callsign(self, ctx, callsign):
        url = f"{self.api_url}/callsign/{callsign}"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @commands.command(name='aircraft_by_reg', help='Get information about an aircraft by its registration.')
    async def aircraft_by_reg(self, ctx, registration):
        url = f"{self.api_url}/reg/{registration}"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @commands.command(name='aircraft_by_type', help='Get information about aircraft by its type.')
    async def aircraft_by_type(self, ctx, aircraft_type):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @commands.command(name='aircraft_by_squawk', help='Get information about an aircraft by its squawk code.')
    async def aircraft_by_squawk(self, ctx, squawk_value):
        url = f"{self.api_url}/squawk/{squawk_value}"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @commands.command(name='military_aircraft', help='Get information about military aircraft.')
    async def military_aircraft(self, ctx):
        url = f"{self.api_url}/mil"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='Military Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving military aircraft information.")

    @commands.command(name='ladd_aircraft', help='Get information about aircraft in LADD (Latin America).')
    async def ladd_aircraft(self, ctx):
        url = f"{self.api_url}/ladd"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='LADD Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving LADD aircraft information.")

    @commands.command(name='pia_aircraft', help='Get information about PIA (Pakistan International Airlines) aircraft.')
    async def pia_aircraft(self, ctx):
        url = f"{self.api_url}/pia"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='PIA Aircraft Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving PIA aircraft information.")

    @commands.command(name='aircraft_within_radius', help='Get information about aircraft within a specified radius.')
    async def aircraft_within_radius(self, ctx, lat, lon, radius):
        url = f"{self.api_url}/point/{lat}/{lon}/{radius}"
        response = self._make_request(url)
        if response:
            formatted_response = self._format_response(response)
            embed = discord.Embed(title='Aircraft Within Radius Information', description=formatted_response, color=0x3498db)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error retrieving aircraft information within the specified radius.")

    @commands.command(name='set_max_requests', help='Set the maximum number of requests the bot can make to the API.')
    @commands.is_owner()
    async def set_max_requests(self, ctx, max_requests: int):
        self.max_requests_per_user = max_requests
        await ctx.send(f"Maximum requests per user set to {max_requests}.")

    def _make_request(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return None  # Return None to indicate an error
        except Exception as e:
            return None

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

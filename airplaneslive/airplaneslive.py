import discord
from redbot.core import commands
import httpx

class Airplaneslive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.airplanes.live/v2"
        self.max_requests_per_user = 10
        self.EMBED_COLOR = discord.Color.blue()  # Replace with your preferred color

    async def _make_request(self, url):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                print(f"Error making request: {e}")
                return None

    async def _get_aircraft_image(self, registration):
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.planespotters.net/pub/photos/reg/{registration}/photos/0"
                print("Image API URL:", url)  # Debugging print
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if 'error' in data:
                        print(f"Error fetching aircraft image: {data['error']}")
                        return None
                    photos = data.get('photos', [])
                    if photos:
                        photo = photos[0]
                        thumbnail = photo.get('thumbnail', {}).get('src')
                        return thumbnail
                return None
        except Exception as e:
            print(f"Error fetching aircraft image: {e}")
            return None

    async def _send_aircraft_info(self, ctx, response):
        formatted_response = self._format_response(response)
        embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=self.EMBED_COLOR)
        if 'ac' in response and response['ac']:
            registration = response['ac'][0].get('reg', '')
            image_url = await self._get_aircraft_image(registration)
            print("Image URL:", image_url)  # Print image URL for debugging
            if image_url:
                embed.set_image(url=https://www.planespotters.net/photo/1284674/ln-one-bristow-norway-as-sikorsky-s-92a)  # Set image of the embed
        embed.set_footer(text="Powered by airplanes.live ✈️")
        await ctx.send(embed=embed)

    def _format_response(self, response):
        if 'ac' in response and response['ac']:
            aircraft_data = response['ac'][0]
            formatted_data = (
                f"**Flight:** {aircraft_data.get('flight', 'N/A').strip()}\n"
                f"**Type:** {aircraft_data.get('desc', 'N/A')} ({aircraft_data.get('t', 'N/A')})\n"
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

    @commands.group(name='aircraft', help='Get information about aircraft.')
    async def aircraft_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid aircraft command passed.')

    @aircraft_group.command(name='hex', help='Get information about an aircraft by its hexadecimal identifier.')
    async def aircraft_by_hex(self, ctx, hex_id):
        url = f"{self.api_url}/hex/{hex_id}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='callsign', help='Get information about an aircraft by its callsign.')
    async def aircraft_by_callsign(self, ctx, callsign):
        url = f"{self.api_url}/callsign/{callsign}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("No aircraft found with the specified callsign.")

    @aircraft_group.command(name='reg', help='Get information about an aircraft by its registration.')
    async def aircraft_by_reg(self, ctx, registration):
        url = f"{self.api_url}/reg/{registration}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='type', help='Get information about aircraft by its type.')
    async def aircraft_by_type(self, ctx, aircraft_type):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='squawk', help='Get information about an aircraft by its squawk code.')
    async def aircraft_by_squawk(self, ctx, squawk_value):
        url = f"{self.api_url}/squawk/{squawk_value}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='military', help= 'military aircraft')
    async def military_aircraft(self, ctx):
        url = f"{self.api_url}/mil"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving military aircraft information.")

    @aircraft_group.command(name='ladd_aircraft', help='Limiting Aircraft Data Displayed (LADD)')
    async def ladd_aircraft(self, ctx):
        url = f"{self.api_url}/ladd"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving LADD aircraft information.")

    @aircraft_group.command(name='pia', help='Privacy ICAO Address.')
    async def pia_aircraft(self, ctx):
        url = f"{self.api_url}/pia"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving PIA aircraft information.")

    @aircraft_group.command(name='radius', help='Get information about aircraft within a specified radius.')
    async def aircraft_within_radius(self, ctx, lat, lon, radius):
        url = f"{self.api_url}/point/{lat}/{lon}/{radius}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information within the specified radius.")

    @commands.command(name='aircraft_to_json', help='Get aircraft information in JSON format.')
    async def aircraft_to_json(self, ctx, aircraft_type):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = await self._make_request(url)
        if response:
            aircraft_info = self._format_response(response)
            json_data = json.dumps(aircraft_info, indent=4)
            await ctx.send(f"```json\n{json_data}\n```")
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='api', help='Set the maximum number of requests the bot can make to the API.')
    @commands.is_owner()
    async def set_max_requests(self, ctx, max_requests: int):
        self.max_requests_per_user = max_requests
        await ctx.send(f"Maximum requests per user set to {max_requests}.")


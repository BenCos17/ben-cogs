import discord
from redbot.core import commands, Config
import json
import aiohttp
import re

class Airplaneslive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.api_url = "https://api.airplanes.live/v2"
        self.max_requests_per_user = 10
        self.EMBED_COLOR = discord.Color.blue() 

    async def cog_unload(self):
        if hasattr(self, '_http_client'):
            await self._http_client.close()

    async def _make_request(self, url):
        if not hasattr(self, '_http_client'):
            self._http_client = aiohttp.ClientSession()
        try:
            async with self._http_client.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error making request: {e}")
            return None

    async def _send_aircraft_info(self, ctx, response):
        if 'ac' in response and response['ac']:                                            
            formatted_response = self._format_response(response)
            hex_id = response['ac'][0].get('hex', '')                                      
            image_url, photographer = await self._get_photo_by_hex(hex_id)
            link = f"[View on airplanes.live](https://globe.airplanes.live/?icao={hex_id})"  # Link to airplanes.live globe view
            formatted_response += f"\n\n{link}"  # Append the link to the end of the response
            embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=self.EMBED_COLOR)
            if image_url:
                embed.set_image(url=image_url)
                embed.set_footer(text="Powered by Planespotters.net and airplanes.live ✈️")
            await ctx.send(embed=embed)
        else:
            await ctx.send("No aircraft information found or the response format is incorrect. \n the plane may be not currently in use or the data is not available at the moment")

    async def _get_photo_by_hex(self, hex_id):
        if not hasattr(self, '_http_client'):
            self._http_client = aiohttp.ClientSession()
        try:
            async with self._http_client.get(f'https://api.planespotters.net/pub/photos/hex/{hex_id}') as response:
                if response.status == 200:
                    json_out = await response.json()
                    if 'photos' in json_out and json_out['photos']:
                        photo = json_out['photos'][0]
                        url = photo.get('thumbnail_large', {}).get('src', '')
                        photographer = photo.get('photographer', '')
                        return url, photographer
        except (KeyError, IndexError, aiohttp.ClientError):
            pass
        return None, None

    def _format_response(self, response):
        if 'ac' in response and response['ac']:
            aircraft_data = response['ac'][0]
            formatted_data = (
                f"**Flight:** {aircraft_data.get('flight', 'N/A').strip()}\n"
                f"**Type:** {aircraft_data.get('desc', 'N/A')} ({aircraft_data.get('t', 'N/A')})\n"
                f"**Altitude:** {aircraft_data.get('alt_baro', 'N/A')} feet\n"
                f"**Ground Speed:** {aircraft_data.get('gs', 'N/A')} knots\n"
                f"**Heading:** {aircraft_data.get('true_heading', 'N/A')} degrees\n"
                f"**Position:** {aircraft_data.get('lat', 'N/A')}, {aircraft_data.get('lon', 'N/A')}\n"
                f"**Squawk:** {aircraft_data.get('squawk', 'N/A')}\n"
                f"**Emergency:** {aircraft_data.get('emergency', 'N/A')}\n"
                f"**Operator:** {aircraft_data.get('ownOp', 'N/A')}\n"
                f"**Year:** {aircraft_data.get('year', 'N/A')}\n"
                f"**Category:** {aircraft_data.get('category', 'N/A')}\n"
                f"**Aircraft Type:** {aircraft_data.get('t', 'N/A')}\n"
                f"**Speed:** {aircraft_data.get('gs', 'N/A')} knots\n"
                f"**Altitude Rate:** {aircraft_data.get('baro_rate', 'N/A')} feet/minute\n"
                f"**Vertical Rate:** {aircraft_data.get('geom_rate', 'N/A')} feet/minute\n"
            )
            return formatted_data
        else:
            return "No aircraft found with the specified callsign."

    @commands.hybrid_group(name='aircraft', help='Get information about aircraft.')
    async def aircraft_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid aircraft command passed.')

    @commands.command(name='configure_alerts', help='Configure custom alerts for specific aircraft data.')
    async def configure_alerts(self, ctx, identifier_type: str, identifier_value: str, alert_type: str, force_update: bool = False):
        """Allows users to configure custom alerts based on specific aircraft data."""
        user_id = ctx.author.id
        config_data = await self.config.user_from_id(int(user_id)).alerts() or {}
        if identifier_type not in ["hex", "squawk", "callsign", "type"]:
            await ctx.send("Invalid identifier type specified. Use one of: hex, squawk, callsign, or type.")
            return
        if alert_type not in ["emergency", "all"]:
            await ctx.send("Invalid alert type specified. Use one of: emergency, all.")
            return
        # Create or update the alert configuration for the user
        if identifier_type not in config_data or force_update:
            config_data[identifier_type] = {}
        config_data[identifier_type][identifier_value] = alert_type
        await self.config.user_from_id(int(user_id)).alerts.set(config_data)
        await ctx.send(f"Alert for {identifier_type} {identifier_value} configured successfully.")

    @configure_alerts.command(name='force_update', help='Force update the alert configuration for specific aircraft data.')
    async def force_update(self, ctx, identifier_type: str, identifier_value: str, alert_type: str):
        """Force update the alert configuration for specific aircraft data."""
        await self.configure_alerts(ctx, identifier_type, identifier_value, alert_type, force_update=True)

    async def check_for_alerts(self, aircraft_data):
        """Check if the received aircraft data matches any user-configured alerts."""
        for user_id, user_alerts in (await self.config.all_users()).items() or {}:
            for identifier_type, identifiers in user_alerts.get('alerts', {}).items() or {}:
                for identifier, alert_type in identifiers.items() or {}:
                    if identifier_type in aircraft_data and aircraft_data[identifier_type] == identifier:
                        if alert_type == "all" or (alert_type == "emergency" and aircraft_data.get("emergency", "") != ""):
                            user = self.bot.get_user(int(user_id))
                            if user:
                                await user.send(f"🚨 Alert Triggered for {identifier_type} {identifier}: {aircraft_data}")
                                break  # Stop checking other alerts for this user to avoid duplicate messages

    @commands.Cog.listener()
    async def on_aircraft_data_received(self, aircraft_data):
        """Listener to process received aircraft data and check for any alerts."""
        await self.check_for_alerts(aircraft_data)

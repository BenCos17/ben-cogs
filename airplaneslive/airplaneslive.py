import discord
from redbot.core import commands, Config
import httpx       #used for the actual lookup commands 
import json        #used for json command
import aiohttp     #used for stats command 

class Airplaneslive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        default_global = {
            'alerts': []
        }
        self.config.register_global(**default_global)
        self.api_url = "https://api.airplanes.live/v2"
        self.planespotters_api_url = "https://api.planespotters.net/pub/photos"
        self.max_requests_per_user = 10
        self.EMBED_COLOR = discord.Color.blue()  #sets embed color to blue 
        self.alert_check_interval = 60
        self.bot.loop.create_task(self.check_alerts())

    async def _make_request(self, url):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                print(f"Error making request: {e}")
                return None

    async def _send_aircraft_info(self, ctx, response):
        if 'ac' in response and response['ac']:                                            # Check if 'ac' key exists and is not empty
            formatted_response = self._format_response(response)
            hex_id = response['ac'][0].get('hex', '')                                      # Extracts hex ID from command
            image_url, photographer = await self._get_photo_by_hex(hex_id)
            embed = discord.Embed(title='Aircraft Information', description=formatted_response, color=self.EMBED_COLOR)
            if image_url:
                embed.set_image(url=image_url)
                embed.set_footer(text=f"Powered by Planespotters.net and airplanes.live ✈️")
            await ctx.send(embed=embed)
        else:
            await ctx.send("No aircraft information found or the response format is incorrect.")

    async def _get_photo_by_hex(self, hex_id):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f'https://api.planespotters.net/pub/photos/hex/{hex_id}')     #image method for planespotters.net embed images
                if response.status_code == 200:
                    json_out = response.json()
                    if 'photos' in json_out and json_out['photos']:
                        photo = json_out['photos'][0]
                        url = photo.get('thumbnail_large', {}).get('src', '')
                        photographer = photo.get('photographer', '')
                        return url, photographer
            except (KeyError, IndexError, httpx.RequestError):
                pass
        return None, None

                                            #formats the response from command ran


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

    @aircraft_group.command(name='military', help='Get information about military aircraft.')
    async def military_aircraft(self, ctx):
        url = f"{self.api_url}/mil"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving military aircraft information.")

    @aircraft_group.command(name='ladd', help='Limiting Aircraft Data Displayed (LADD).')
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

    @aircraft_group.command(name='json', help='Get aircraft information in JSON format.')
    async def json(self, ctx, aircraft_type):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = await self._make_request(url)
        if response:
            aircraft_info = self._format_response(response)
            json_data = json.dumps(aircraft_info, indent=4)
            await ctx.send(f"```json\n{json_data}\n```")
        else:
            await ctx.send("Error retrieving aircraft information.")


                    #sets max api requests from airplanes.live and allows user to change it if they own the bot 

    @aircraft_group.command(name='api', help='Set the maximum number of requests the bot can make to the API.')
    @commands.is_owner()
    async def set_max_requests(self, ctx, max_requests: int):
        self.max_requests_per_user = max_requests
        await ctx.send(f"Maximum requests per user set to {max_requests}.")

    @aircraft_group.command(name='stats', help='Get https://airplanes.live feeder stats.')
    async def stats(self, ctx):
        url = "https://api.airplanes.live/stats"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            if "beast" in data and "mlat" in data and "other" in data and "aircraft" in data:
                beast_stats = data["beast"]
                mlat_stats = data["mlat"]
                other_stats = data["other"]
                aircraft_stats = data["aircraft"]

                embed = discord.Embed(title="airplanes.live Stats", color=0x00ff00)
                embed.set_thumbnail(url="https://airplanes.live/img/airplanes-live-logo.png")
                embed.add_field(name="Beast", value=beast_stats, inline=False)
                embed.add_field(name="MLAT", value=mlat_stats, inline=False)
                embed.add_field(name="Other", value=other_stats, inline=False)
                embed.add_field(name="Aircraft", value=aircraft_stats, inline=False)

                await ctx.send(embed=embed)
            else:
                await ctx.send("Incomplete data received from API.")
        except aiohttp.ClientError as e:
            await ctx.send(f"Error fetching data: {e}")

    @aircraft_group.command(name='set_alert', help='Set up alerts for planes in a specific channel.')
    async def set_alert(self, ctx, hex_id: str, channel: discord.TextChannel):
        alerts = await self.config.alerts()
        alert_data = {
            'hex_id': hex_id,
            'channel_id': channel.id
        }
        alerts.append(alert_data)
        await self.config.alerts.set(alerts)
        await ctx.send(f"Alert for aircraft with hex ID {hex_id} set in channel {channel.mention}.")

    @aircraft_group.command(name='list_alerts', help='List all active alerts.')
    async def list_alerts(self, ctx):
        alerts = await self.config.alerts()
        if alerts:
            alert_list = "\n".join([f"Hex ID: {alert['hex_id']}, Channel: <#{alert['channel_id']}>" for alert in alerts])
            await ctx.send(f"Active alerts:\n{alert_list}")
        else:
            await ctx.send("No active alerts found.")

    @aircraft_group.command(name='remove_alert', help='Remove an active alert.')
    async def remove_alert(self, ctx, hex_id: str):
        alerts = await self.config.alerts()
        for alert in alerts:
            if alert['hex_id'] == hex_id:
                alerts.remove(alert)
                await self.config.alerts.set(alerts)
                await ctx.send(f"Alert for aircraft with hex ID {hex_id} removed successfully.")
                return
        await ctx.send(f"No active alert found for aircraft with hex ID {hex_id}.")

    async def check_alerts(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                live_data = await self._make_request(f"{self.api_url}/all")

                if live_data and 'ac' in live_data:
                    for aircraft in live_data['ac']:
                        hex_id = aircraft.get('hex', '')
                        alerts = await self.config.alerts()
                        for alert in alerts:
                            if alert['hex_id'] == hex_id:
                                channel = self.bot.get_channel(alert['channel_id'])
                                if channel:
                                    formatted_response = self._format_response(aircraft)
                                    await channel.send(f"Alert: Aircraft with hex ID {hex_id} detected.\n{formatted_response}")

                await asyncio.sleep(self.alert_check_interval)
            except Exception as e:
                print(f"Error checking alerts: {e}")
                await asyncio.sleep(self.alert_check_interval)


#list all setup alerts in server

    @aircraft_group.command(name='list_alerts', help='List all active alerts.')
    async def list_alerts(self, ctx):
        """List all active alerts."""
        alerts = await self.config.alerts()
        if alerts:
            alert_list = "\n".join([f"Hex ID: {alert['hex_id']}, Channel: <#{alert['channel_id']}>" for alert in alerts])
            await ctx.send(f"Active alerts:\n{alert_list}")
        else:
            await ctx.send("No active alerts found.")

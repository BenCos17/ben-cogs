import discord #type: ignore
import aiohttp #type: ignore
import re
import asyncio
import urllib
import os
import io
import tempfile
import csv
import datetime
from urllib.parse import quote_plus
from discord.ext import tasks, commands #type: ignore
from redbot.core import commands, Config #type: ignore
from reportlab.lib.pagesizes import letter, landscape, A4 #type: ignore
from reportlab.pdfgen import canvas #type: ignore 
from reportlab.lib import colors #type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle #type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle #type: ignore

import skysearch #type: ignore
from .icao_codes import law_enforcement_icao_set, military_icao_set, medical_icao_set, suspicious_icao_set, newsagency_icao_set, balloons_icao_set, global_prior_known_accident_set, ukr_conflict_set, agri_utility_set

class Skysearch(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.config.register_global(airplanesliveapi=None)  # API key for airplanes.live
        self.config.register_guild(alert_channel=None, alert_role=None, auto_icao=False, last_emergency_squawk_time=None)
        self.api_url = "https://rest.api.airplanes.live"  # Updated to new REST API base URL
        self.max_requests_per_user = 10
        self.EMBED_COLOR = discord.Color(0xfffffe)
        self.check_emergency_squawks.start()
        self.law_enforcement_icao_set = law_enforcement_icao_set
        self.military_icao_set = military_icao_set
        self.medical_icao_set = medical_icao_set
        self.suspicious_icao_set = suspicious_icao_set
        self.newsagency_icao_set = newsagency_icao_set
        self.balloons_icao_set = balloons_icao_set
        self.global_prior_known_accident_set = global_prior_known_accident_set
        self.ukr_conflict_set = ukr_conflict_set
        self.agri_utility_set = agri_utility_set
        
    async def cog_unload(self):
        if hasattr(self, '_http_client'):
            await self._http_client.close()

    async def _get_headers(self):
        """Return headers with API key for requests, if available."""
        headers = {}
        api_key = await self.config.airplanesliveapi()
        if api_key:
            headers['auth'] = api_key  # Use 'auth' header as specified in API docs
        return headers

    async def _make_request(self, url, ctx=None):
        if not hasattr(self, '_http_client'):
            self._http_client = aiohttp.ClientSession()
        try:
            headers = await self._get_headers()  # Get headers with API key if available
            
            async with self._http_client.get(url, headers=headers) as response:
                if response.status == 401:
                    error_msg = "API key authentication failed. Please check your API key."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    return None
                elif response.status == 403:
                    error_msg = "API key does not have permission for this endpoint."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    return None
                elif response.status == 429:
                    error_msg = "Rate limit exceeded. Please wait before making more requests."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    return None
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            error_msg = f"Error making request: {e}"
            if ctx:
                await ctx.send(f"❌ **Error:** {error_msg}")
            else:
                print(error_msg)
            return None

    async def _send_aircraft_info(self, ctx, response):
        if 'aircraft' in response and response['aircraft']:
            await ctx.typing()
            aircraft_data = response['aircraft'][0]
            emergency_squawk_codes = ['7500', '7600', '7700']
            hex_id = aircraft_data.get('hex', '')                                      
            image_url, photographer = await self._get_photo_by_hex(hex_id)
            registration = aircraft_data.get('reg', '')  # Get the registration for image fetching
            link = f"https://globe.airplanes.live/?icao={hex_id}"
            squawk_code = aircraft_data.get('squawk', 'N/A')
            description = f"{aircraft_data.get('desc', 'N/A')}"
            if aircraft_data.get('year', None) is not None:
                description += f" ({aircraft_data.get('year')})"
            if squawk_code == '7500':
                embed = discord.Embed(title=description, color=0xff4545)
                emergency_status = "Aircraft reports it's been hijacked"
            elif squawk_code == '7600':
                embed = discord.Embed(title=description, color=0xff4545)
                emergency_status = "Aircraft has lost radio contact"
            elif squawk_code == '7700':
                embed = discord.Embed(title=description, color=0xff4545)
                emergency_status = "Aircraft has declared a general emergency"
            else:
                embed = discord.Embed(title=description, color=0xfffffe)
                emergency_status = "Aircraft reports normal conditions"
            callsign = aircraft_data.get('flight', 'N/A').strip()
            if not callsign or callsign == 'N/A':
                callsign = 'BLOCKED'
            embed.add_field(name="Callsign", value=f"{callsign}", inline=True)
            registration = aircraft_data.get('reg', None)
            if registration is not None:
                registration = registration.upper()
                embed.add_field(name="Registration", value=f"{registration}", inline=True)
            icao = aircraft_data.get('hex', 'N/A').upper()
            embed.add_field(name="ICAO", value=f"{icao}", inline=True)
            altitude = aircraft_data.get('alt_baro', 'N/A')
            if altitude == 'ground':
                embed.add_field(name="Status", value="On ground", inline=True)
            elif altitude != 'N/A':
                if isinstance(altitude, int):
                    altitude = "{:,}".format(altitude)
                altitude_feet = f"{altitude} ft"
                embed.add_field(name="Altitude", value=f"{altitude_feet}", inline=True)
            heading = aircraft_data.get('true_heading', None)
            if heading is not None:
                if 0 <= heading < 45:
                    emoji = ":arrow_upper_right:"
                elif 45 <= heading < 90:
                    emoji = ":arrow_right:"
                elif 90 <= heading < 135:
                    emoji = ":arrow_lower_right:"
                elif 135 <= heading < 180:
                    emoji = ":arrow_down:"
                elif 180 <= heading < 225:
                    emoji = ":arrow_lower_left:"
                elif 225 <= heading < 270:
                    emoji = ":arrow_left:"
                elif 270 <= heading < 315:
                    emoji = ":arrow_upper_left:"
                else:
                    emoji = ":arrow_up:"
                embed.add_field(name="Heading", value=f"{emoji} {heading}°", inline=True)
            lat = aircraft_data.get('lat', 'N/A')
            lon = aircraft_data.get('lon', 'N/A')
            if lat != 'N/A':
                lat = round(float(lat), 2)
                lat_dir = "N" if lat >= 0 else "S"
                lat = f"{abs(lat)}{lat_dir}"
            if lon != 'N/A':
                lon = round(float(lon), 2)
                lon_dir = "E" if lon >= 0 else "W"
                lon = f"{abs(lon)}{lon_dir}"
            if lat != 'N/A' and lon != 'N/A':
                embed.add_field(name="Position", value=f"- {lat}\n- {lon}", inline=True)
            embed.add_field(name="Squawk", value=f"{aircraft_data.get('squawk', 'BLOCKED')}", inline=True)
            
            aircraft_model = aircraft_data.get('t', None)
            if aircraft_model is not None:
                embed.add_field(name="Model", value=f"{aircraft_model}", inline=True)
            ground_speed_knots = aircraft_data.get('gs', 'N/A')
            if ground_speed_knots != 'N/A':
                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
                embed.add_field(name="Speed", value=f"{ground_speed_mph} mph", inline=True)
            category_code_to_label = {
                "A0": "No info available",
                "A1": "Light aircraft",
                "A2": "Small aircraft",
                "A3": "Large aircraft",
                "A4": "High vortex large aircraft",
                "A5": "Heavy aircraft",
                "A6": "High performance aircraft",
                "A7": "Rotorcraft",
                "B0": "No info available",
                "B1": "Glider / sailplane",
                "B2": "Lighter-than-air",
                "B3": "Parachutist / skydiver",
                "B4": "Ultralight / hang-glider / paraglider",
                "B5": "Reserved",
                "B6": "UAV",
                "B7": "Space / trans-atmospheric vehicle",
                "C0": "No info available",
                "C1": "Emergency vehicle",
                "C2": "Service vehicle",
                "C3": "Point obstacle",
                "C4": "Cluster obstacle",
                "C5": "Line obstacle",
                "C6": "Reserved",
                "C7": "Reserved"
            }
            category = aircraft_data.get('category', None)
            if category is not None:
                category_label = category_code_to_label.get(category, "Unknown category")
                embed.add_field(name="Category", value=f"{category_label}", inline=True)

            operator = aircraft_data.get('ownOp', None)
            if operator is not None:
                operator_encoded = quote_plus(operator)
                embed.add_field(name="Operated by", value=f"[{operator}](https://www.google.com/search?q={operator_encoded})", inline=True)
            
            last_seen = aircraft_data.get('seen', 'N/A')
            if last_seen != 'N/A':
                last_seen_text = "Just now" if float(last_seen) < 1 else f"{int(float(last_seen))} seconds ago"
                embed.add_field(name="Last signal", value=last_seen_text, inline=True)
            
            last_seen_pos = aircraft_data.get('seen_pos', 'N/A')
            if last_seen_pos != 'N/A':
                last_seen_pos_text = "Just now" if float(last_seen_pos) < 1 else f"{int(float(last_seen_pos))} seconds ago"
                embed.add_field(name="Last position", value=last_seen_pos_text, inline=True)
            
            baro_rate = aircraft_data.get('baro_rate', 'N/A')
            if baro_rate == 'N/A':
                embed.add_field(name="Altitude trend", value="Altitude trends unavailable, **not enough data**", inline=True)
            else:
                baro_rate_fps = round(int(baro_rate) / 60, 2)  # Convert feet per minute to feet per second
                if abs(baro_rate_fps) < 50/60:
                    embed.add_field(name="Altitude data", value="Maintaining consistent altitude", inline=True)
                elif baro_rate_fps > 0:
                    embed.add_field(name="Altitude data", value=" **Climbing** " + f"{baro_rate_fps} feet/sec", inline=True)
                else:
                    embed.add_field(name="Altitude data", value=" **Descending** " + f"{abs(baro_rate_fps)} feet/sec", inline=True)

            embed.add_field(name="Flight status", value=emergency_status, inline=True)


            icao = aircraft_data.get('hex', None).upper()
            if icao and icao.upper() in self.law_enforcement_icao_set:
                embed.add_field(name="Asset intelligence", value=":police_officer: Known for use by **state law enforcement**", inline=False)
            if icao and icao.upper() in self.military_icao_set:
                embed.add_field(name="Asset intelligence", value=":military_helmet: Known for use in **military** and **government**", inline=False)
            if icao and icao.upper() in self.medical_icao_set:
                embed.add_field(name="Asset intelligence", value=":hospital: Known for use in **medical response** and **transport**", inline=False)
            if icao and icao.upper() in self.suspicious_icao_set:
                embed.add_field(name="Asset intelligence", value=":warning: Exhibits suspicious flight or **surveillance** activity", inline=False)
            if icao and icao.upper() in self.global_prior_known_accident_set:
                embed.add_field(name="Asset intelligence", value=":boom: Prior involved in one or more **documented accidents**", inline=False)
            if icao and icao.upper() in self.ukr_conflict_set:
                embed.add_field(name="Asset intelligence", value=":flag_ua: Utilized within the **[Russo-Ukrainian conflict](https://en.wikipedia.org/wiki/Russian-occupied_territories_of_Ukraine)**", inline=False)
            if icao and icao.upper() in self.newsagency_icao_set:
                embed.add_field(name="Asset intelligence", value=":newspaper: Used by **news** or **media** organization", inline=False)
            if icao and icao.upper() in self.balloons_icao_set:
                embed.add_field(name="Asset intelligence", value=":balloon: Aircraft is a **balloon**", inline=False)
            if icao and icao.upper() in self.agri_utility_set:
                embed.add_field(name="Asset intelligence", value=":corn: Used for **agriculture surveys, easement validation, or land inspection**", inline=False)

            image_url, photographer = await self._get_photo_by_hex(icao)
            if image_url and photographer:
                embed.set_thumbnail(url=image_url)
                embed.set_footer(text=f"Photo by {photographer}")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=f"{link}", style=discord.ButtonStyle.link))
            
            # Ensure ground_speed_mph is defined
            ground_speed_mph = 'unknown'
            if ground_speed_knots != 'N/A':
                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
            
            squawk_code = aircraft_data.get('squawk', 'N/A')
            if squawk_code in emergency_squawk_codes:
                tweet_text = f"Spotted an aircraft declaring an emergency! #Squawk #{squawk_code}, flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. #SkySearch #Emergency\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
            else:
                tweet_text = f"Tracking flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph using #SkySearch\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
            tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote_plus(tweet_text)}"
            view.add_item(discord.ui.Button(label=f"Post on 𝕏", emoji="📣", url=tweet_url, style=discord.ButtonStyle.link))
            whatsapp_text = f"Check out this aircraft! Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. Track live @ https://globe.airplanes.live/?icao={icao} #SkySearch"
            whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote_plus(whatsapp_text)}"
            view.add_item(discord.ui.Button(label="Send on WhatsApp", emoji="📱", url=whatsapp_url, style=discord.ButtonStyle.link))
            await ctx.send(embed=embed, view=view)

        else:
            embed = discord.Embed(title='No results found for your query', color=discord.Colour(0xff4545))
            embed.add_field(name="Details", value="No aircraft information found or the response format is incorrect.", inline=False)
            message = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            try:
                await ctx.message.delete()
            except discord.errors.Forbidden:
                pass
            try:
                await message.delete()
            except discord.errors.Forbidden:
                pass

    async def _get_photo_by_hex(self, hex_id, registration=None):
        if not hasattr(self, '_http_client'):
            self._http_client = aiohttp.ClientSession()
        
        # Fetch photo by hex ICAO
        try:
            async with self._http_client.get(f'https://api.planespotters.net/pub/photos/reg/{hex_id}') as response:
                if response.status == 200:
                    json_out = await response.json()
                    if 'photos' in json_out and json_out['photos']:
                        photo = json_out['photos'][0]
                        url = photo.get('thumbnail_large', {}).get('src', '')
                        photographer = photo.get('photographer', '')
                        return url, photographer  # Return photo for hex ICAO
        except (KeyError, IndexError, aiohttp.ClientError):
            pass

        # Fetch photo by registration if provided
        if registration:
            try:
                async with self._http_client.get(f'https://api.planespotters.net/pub/photos/reg/{registration}') as response:
                    if response.status == 200:
                        json_out = await response.json()
                        if 'photos' in json_out and json_out['photos']:
                            photo = json_out['photos'][0]
                            url = photo.get('thumbnail_large', {}).get('src', '')
                            photographer = photo.get('photographer', '')
                            return url, photographer  # Return photo for registration
            except (KeyError, IndexError, aiohttp.ClientError):
                pass

        return None, None  # Return None if no photo found for both

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
        

    @commands.guild_only()
    @commands.group(name='aircraft', help='Command center for aircraft related commands')
    async def aircraft_group(self, ctx):
        """Command center for aircraft related commands"""
   

    @commands.guild_only()
    @aircraft_group.command(name='icao', help='Get information about an aircraft by its 24-bit ICAO Address')
    async def aircraft_by_icao(self, ctx, hex_id: str):
        # Use new REST API endpoint for ICAO hex lookup
        url = f"{self.api_url}/?find_hex={hex_id}"
        response = await self._make_request(url, ctx)
        if response:
            if 'aircraft' in response and len(response['aircraft']) > 1:
                for aircraft_info in response['aircraft']:
                    await self._send_aircraft_info(ctx, {'aircraft': [aircraft_info]})
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)
    
    @commands.guild_only()
    @aircraft_group.command(name='callsign', help='Get information about an aircraft by its callsign.')
    async def aircraft_by_callsign(self, ctx, callsign: str):
        # Use new REST API endpoint for callsign lookup
        url = f"{self.api_url}/?find_callsign={callsign}"
        response = await self._make_request(url, ctx)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="No aircraft found with the specified callsign.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='reg', help='Get information about an aircraft by its registration.')
    async def aircraft_by_reg(self, ctx, registration: str):
        # Use new REST API endpoint for registration lookup
        url = f"{self.api_url}/?find_reg={registration}"
        response = await self._make_request(url, ctx)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='type', help='Get information about aircraft by its type.')
    async def aircraft_by_type(self, ctx, aircraft_type: str):
        # Use new REST API endpoint for type lookup
        url = f"{self.api_url}/?find_type={aircraft_type}"
        response = await self._make_request(url, ctx)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='squawk', help='Get information about an aircraft by its squawk code.')
    async def aircraft_by_squawk(self, ctx, squawk_value: str):
        # Use new REST API endpoint for squawk filter - must combine with base query
        url = f"{self.api_url}/?all_with_pos&filter_squawk={squawk_value}"
        response = await self._make_request(url, ctx)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='military', help='Get information about military aircraft.')
    async def show_military_aircraft(self, ctx):
        # Use new REST API endpoint for military aircraft - must combine with base query
        url = f"{self.api_url}/?all_with_pos&filter_mil"
        response = await self._make_request(url, ctx)
        if response:
            aircraft_list = response.get('aircraft', [])
            if aircraft_list:
                page_index = 0

                async def create_embed(aircraft):
                    embed = discord.Embed(title=f"Live military aircraft ({page_index + 1} of {len(aircraft_list)})", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    aircraft_description = aircraft.get('desc', 'N/A')  # Aircraft Description
                    aircraft_squawk = aircraft.get('squawk', 'N/A')  # Squawk
                    aircraft_lat = aircraft.get('lat', 'N/A')  # Latitude
                    aircraft_lon = aircraft.get('lon', 'N/A')  # Longitude
                    aircraft_heading = aircraft.get('heading', 'N/A')  # Heading
                    aircraft_speed = aircraft.get('spd', 'N/A')  # Speed
                    aircraft_hex = aircraft.get('hex', 'N/A').upper()  # Hex 

                    embed.description = f"# {aircraft_description}"
                    embed.add_field(name="Squawk", value=f"**`{aircraft_squawk}`**", inline=True)
                    embed.add_field(name="Latitude", value=f"**`{aircraft_lat}`**", inline=True)
                    embed.add_field(name="Longitude", value=f"**`{aircraft_lon}`**", inline=True)
                    embed.add_field(name="Heading", value=f"**`{aircraft_heading}`**", inline=True)
                    embed.add_field(name="Speed", value=f"**`{aircraft_speed}`**", inline=True)
                    embed.add_field(name="ICAO", value=f"**`{aircraft_hex}`**", inline=True)

                    photo_url, photographer = await self._get_photo_by_hex(aircraft_hex)
                    if photo_url:
                        embed.set_image(url=photo_url)
                    if photographer:
                        embed.set_footer(text=f"Photo by {photographer}")

                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label=f"Track {aircraft_hex} live", url=f"https://globe.airplanes.live/?icao={aircraft_hex}"))

                    return embed, view

                async def update_message(message, page_index):
                    embed, view = await create_embed(aircraft_list[page_index])
                    await message.edit(embed=embed, view=view)

                embed, view = await create_embed(aircraft_list[page_index])
                message = await ctx.send(embed=embed, view=view)

                await message.add_reaction("⬅️")
                await message.add_reaction("❌")
                await message.add_reaction("➡️")
                
                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "❌", "➡️"]

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                        if str(reaction.emoji) == "⬅️" and page_index > 0:
                            page_index -= 1
                            await update_message(message, page_index)
                        elif str(reaction.emoji) == "➡️" and page_index < len(aircraft_list) - 1:
                            page_index += 1
                            await update_message(message, page_index)
                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break

                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)
    
    @commands.guild_only()
    @aircraft_group.command(name='ladd', help='Get information on LADD-restricted aircraft')
    async def ladd_aircraft(self, ctx):
        # Use new REST API endpoint for LADD aircraft - must combine with base query
        url = f"{self.api_url}/?all_with_pos&filter_ladd"
        response = await self._make_request(url, ctx)
        if response:
            if 'aircraft' in response and len(response['aircraft']) > 1:
                pages = [response['aircraft'][i:i + 10] for i in range(0, len(response['aircraft']), 10)]  # Split aircraft list into pages of 10
                page_index = 0
                
                while True:
                    embed = discord.Embed(title=f"Limited Aircraft Data Displayed (Page {page_index + 1}/{len(pages)})", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    
                    for aircraft in pages[page_index]:
                        aircraft_description = aircraft.get('desc', 'N/A')  # Aircraft Description
                        aircraft_squawk = aircraft.get('squawk', 'N/A')  # Squawk
                        aircraft_lat = aircraft.get('lat', 'N/A')  # Latitude
                        aircraft_lon = aircraft.get('lon', 'N/A')  # Longitude
                        aircraft_heading = aircraft.get('heading', 'N/A')  # Heading
                        aircraft_speed = aircraft.get('spd', 'N/A')  # Speed
                        aircraft_hex = aircraft.get('hex', 'N/A')  # Hex

                        aircraft_info = f"**Squawk:** {aircraft_squawk}\n"
                        aircraft_info += f"**Coordinates:** Lat: {aircraft_lat}, Lon: {aircraft_lon}\n"
                        aircraft_info += f"**Heading:** {aircraft_heading}\n"
                        aircraft_info += f"**Speed:** {aircraft_speed}\n"
                        aircraft_info += f"**ICAO:** {aircraft_hex}"

                        embed.add_field(name=aircraft_description, value=aircraft_info, inline=False)

                    message = await ctx.send(embed=embed)
                    await message.add_reaction("⬅️")  # Adding a reaction to scroll to the previous page
                    await message.add_reaction("❌")  # Adding a reaction to close
                    await message.add_reaction("➡️")  # Adding a reaction to scroll to the next page

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ['⬅️', '❌', '➡️']

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        await message.remove_reaction(reaction, user)
                        
                        if str(reaction.emoji) == '⬅️' and page_index > 0:
                            await message.delete()
                            page_index -= 1
                        elif str(reaction.emoji) == '➡️' and page_index < len(pages) - 1:
                            await message.delete()
                            page_index += 1
                        elif str(reaction.emoji) == '❌':
                            await message.delete()
                            break
                        else:
                            await message.delete()
                            break
                    except asyncio.TimeoutError:
                        await message.delete()
                        break
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='pia', help='View live aircraft using private ICAO addresses')
    async def pia_aircraft(self, ctx):
        # Use new REST API endpoint for PIA aircraft - must combine with base query
        url = f"{self.api_url}/?all_with_pos&filter_pia"
        response = await self._make_request(url, ctx)
        if response:
            if 'aircraft' in response and len(response['aircraft']) > 1:
                pages = [response['aircraft'][i:i + 10] for i in range(0, len(response['aircraft']), 10)]  # Split aircraft list into pages of 10
                page_index = 0
                
                while True:
                    embed = discord.Embed(title=f"Private ICAO Aircraft Data Displayed (Page {page_index + 1}/{len(pages)})", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    
                    for aircraft in pages[page_index]:
                        aircraft_description = aircraft.get('desc', 'N/A')  # Aircraft Description
                        aircraft_squawk = aircraft.get('squawk', 'N/A')  # Squawk
                        aircraft_lat = aircraft.get('lat', 'N/A')  # Latitude
                        aircraft_lon = aircraft.get('lon', 'N/A')  # Longitude
                        aircraft_heading = aircraft.get('heading', 'N/A')  # Heading
                        aircraft_speed = aircraft.get('spd', 'N/A')  # Speed
                        aircraft_hex = aircraft.get('hex', 'N/A')  # Hex

                        aircraft_info = f"**Squawk:** {aircraft_squawk}\n"
                        aircraft_info += f"**Coordinates:** Lat: {aircraft_lat}, Lon: {aircraft_lon}\n"
                        aircraft_info += f"**Heading:** {aircraft_heading}\n"
                        aircraft_info += f"**Speed:** {aircraft_speed}\n"
                        aircraft_info += f"**ICAO:** {aircraft_hex}"

                        embed.add_field(name=aircraft_description, value=aircraft_info, inline=False)

                    message = await ctx.send(embed=embed)
                    await message.add_reaction("⬅️")  # Adding a reaction to scroll to the previous page
                    await message.add_reaction("❌")  # Adding a reaction to close
                    await message.add_reaction("➡️")  # Adding a reaction to scroll to the next page

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ['⬅️', '❌', '➡️']

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        await message.remove_reaction(reaction, user)
                        
                        if str(reaction.emoji) == '⬅️' and page_index > 0:
                            await message.delete()
                            page_index -= 1
                        elif str(reaction.emoji) == '➡️' and page_index < len(pages) - 1:
                            await message.delete()
                            page_index += 1
                        elif str(reaction.emoji) == '❌':
                            await message.delete()
                            break
                        else:
                            await message.delete()
                            break
                    except asyncio.TimeoutError:
                        await message.delete()
                        break
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='radius', help='Get information about aircraft within a specified radius.')
    async def aircraft_within_radius(self, ctx, lat: str, lon: str, radius: str):
        # Use new REST API endpoint for circle search
        url = f"{self.api_url}/?circle={lat},{lon},{radius}"
        response = await self._make_request(url, ctx)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information for aircraft within the specified radius.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='closest', help='Find the closest aircraft to specified coordinates.')
    async def closest_aircraft(self, ctx, lat: str, lon: str, radius: str = "100"):
        # Validate input parameters
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            radius_float = float(radius)
            
            if not (-90 <= lat_float <= 90):
                embed = discord.Embed(title="Error", description="Latitude must be between -90 and 90 degrees.", color=0xff4545)
                await ctx.send(embed=embed)
                return
                
            if not (-180 <= lon_float <= 180):
                embed = discord.Embed(title="Error", description="Longitude must be between -180 and 180 degrees.", color=0xff4545)
                await ctx.send(embed=embed)
                return
                
            if radius_float <= 0 or radius_float > 500:
                embed = discord.Embed(title="Error", description="Radius must be between 0 and 500 nautical miles.", color=0xff4545)
                await ctx.send(embed=embed)
                return
                
        except ValueError:
            embed = discord.Embed(title="Error", description="Invalid coordinates or radius. Please provide valid numbers.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        # Use new REST API endpoint for closest aircraft search
        url = f"{self.api_url}/?closest={lat},{lon},{radius}"
        response = await self._make_request(url, ctx)
        
        if response and 'aircraft' in response and response['aircraft']:
            aircraft_data = response['aircraft'][0]
            
            # Create a custom embed for closest aircraft with distance info
            embed = discord.Embed(title="Closest Aircraft Found", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            
            # Add distance information if available
            distance_nmi = aircraft_data.get('dst', 'Unknown')
            direction_deg = aircraft_data.get('dir', 'Unknown')
            
            if distance_nmi != 'Unknown' and direction_deg != 'Unknown':
                embed.description = f"**Distance:** {distance_nmi:.1f} nautical miles\n**Direction:** {direction_deg}° from your location"
            
            # Aircraft description
            description = f"{aircraft_data.get('desc', 'N/A')}"
            if aircraft_data.get('year', None) is not None:
                description += f" ({aircraft_data.get('year')})"
            embed.add_field(name="Aircraft", value=description, inline=False)
            
            # Basic aircraft info
            callsign = aircraft_data.get('flight', 'N/A').strip()
            if not callsign or callsign == 'N/A':
                callsign = 'BLOCKED'
            embed.add_field(name="Callsign", value=f"{callsign}", inline=True)
            
            registration = aircraft_data.get('reg', None)
            if registration is not None:
                registration = registration.upper()
                embed.add_field(name="Registration", value=f"{registration}", inline=True)
            
            icao = aircraft_data.get('hex', 'N/A').upper()
            embed.add_field(name="ICAO", value=f"{icao}", inline=True)
            
            # Position
            lat_pos = aircraft_data.get('lat', 'N/A')
            lon_pos = aircraft_data.get('lon', 'N/A')
            if lat_pos != 'N/A' and lon_pos != 'N/A':
                lat_formatted = round(float(lat_pos), 4)
                lon_formatted = round(float(lon_pos), 4)
                embed.add_field(name="Position", value=f"{lat_formatted}, {lon_formatted}", inline=True)
            
            # Altitude
            altitude = aircraft_data.get('alt_baro', 'N/A')
            if altitude == 'ground':
                embed.add_field(name="Status", value="On ground", inline=True)
            elif altitude != 'N/A':
                if isinstance(altitude, int):
                    altitude = "{:,}".format(altitude)
                altitude_feet = f"{altitude} ft"
                embed.add_field(name="Altitude", value=f"{altitude_feet}", inline=True)
            
            # Speed
            ground_speed_knots = aircraft_data.get('gs', 'N/A')
            if ground_speed_knots != 'N/A':
                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
                embed.add_field(name="Speed", value=f"{ground_speed_mph} mph", inline=True)
            
            # Squawk
            squawk_code = aircraft_data.get('squawk', 'N/A')
            embed.add_field(name="Squawk", value=f"{squawk_code}", inline=True)
            
            # Emergency status
            emergency_squawk_codes = ['7500', '7600', '7700']
            if squawk_code in emergency_squawk_codes:
                if squawk_code == '7500':
                    emergency_status = "🚨 Aircraft reports it's been hijacked"
                elif squawk_code == '7600':
                    emergency_status = "🚨 Aircraft has lost radio contact"
                elif squawk_code == '7700':
                    emergency_status = "🚨 Aircraft has declared a general emergency"
                embed.add_field(name="Emergency Status", value=emergency_status, inline=False)
            
            # Asset intelligence
            if icao and icao.upper() in self.law_enforcement_icao_set:
                embed.add_field(name="Asset intelligence", value=":police_officer: Known for use by **state law enforcement**", inline=False)
            if icao and icao.upper() in self.military_icao_set:
                embed.add_field(name="Asset intelligence", value=":military_helmet: Known for use in **military** and **government**", inline=False)
            if icao and icao.upper() in self.medical_icao_set:
                embed.add_field(name="Asset intelligence", value=":hospital: Known for use in **medical response** and **transport**", inline=False)
            if icao and icao.upper() in self.suspicious_icao_set:
                embed.add_field(name="Asset intelligence", value=":warning: Exhibits suspicious flight or **surveillance** activity", inline=False)
            if icao and icao.upper() in self.global_prior_known_accident_set:
                embed.add_field(name="Asset intelligence", value=":boom: Prior involved in one or more **documented accidents**", inline=False)
            if icao and icao.upper() in self.ukr_conflict_set:
                embed.add_field(name="Asset intelligence", value=":flag_ua: Utilized within the **[Russo-Ukrainian conflict](https://en.wikipedia.org/wiki/Russian-occupied_territories_of_Ukraine)**", inline=False)
            if icao and icao.upper() in self.newsagency_icao_set:
                embed.add_field(name="Asset intelligence", value=":newspaper: Used by **news** or **media** organization", inline=False)
            if icao and icao.upper() in self.balloons_icao_set:
                embed.add_field(name="Asset intelligence", value=":balloon: Aircraft is a **balloon**", inline=False)
            if icao and icao.upper() in self.agri_utility_set:
                embed.add_field(name="Asset intelligence", value=":corn: Used for **agriculture surveys, easement validation, or land inspection**", inline=False)
            
            # Add photo if available
            image_url, photographer = await self._get_photo_by_hex(icao)
            if image_url and photographer:
                embed.set_thumbnail(url=image_url)
                embed.set_footer(text=f"Photo by {photographer}")
            
            # Create view with buttons
            view = discord.ui.View()
            link = f"https://globe.airplanes.live/?icao={icao}"
            view.add_item(discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=link, style=discord.ButtonStyle.link))
            
            # Add tracking button
            view.add_item(discord.ui.Button(label="Track Live", emoji="✈️", url=link, style=discord.ButtonStyle.link))
            
            await ctx.send(embed=embed, view=view)
            
        elif response and 'aircraft' in response and not response['aircraft']:
            embed = discord.Embed(title="No Aircraft Found", description=f"No aircraft found within {radius} nautical miles of the specified location.", color=0xff4545)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving closest aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='export', help='Search aircraft by ICAO, callsign, squawk, or type and export the results.')
    async def export_aircraft(self, ctx, search_type: str, search_value: str, file_format: str):
        # Map search_type to new REST API query parameters
        if search_type not in ["icao", "callsign", "squawk", "type"]:
            embed = discord.Embed(title="Error", description="Invalid search type specified. Use one of: icao, callsign, squawk, or type.", color=0xfa4545)
            await ctx.send(embed=embed)
            return

        if search_type == "icao":
            url = f"{self.api_url}/?find_hex={search_value}"
        elif search_type == "callsign":
            url = f"{self.api_url}/?find_callsign={search_value}"
        elif search_type == "squawk":
            url = f"{self.api_url}/?all_with_pos&filter_squawk={search_value}"
        elif search_type == "type":
            url = f"{self.api_url}/?find_type={search_value}"
        else:
            embed = discord.Embed(title="Error", description="Invalid search type specified.", color=0xfa4545)
            await ctx.send(embed=embed)
            return

        response = await self._make_request(url, ctx)
        if response:
            if file_format not in ["csv", "pdf", "txt", "html"]:
                embed = discord.Embed(title="Error", description="Invalid file format specified. Use one of: csv, pdf, txt, or html.", color=0xfa4545)
                await ctx.send(embed=embed)
                return

            if not response.get('aircraft'):
                embed = discord.Embed(title="Error", description="No aircraft data found.", color=0xfa4545)
                await ctx.send(embed=embed)
                return

            file_name = f"{search_type}_{search_value}.{file_format.lower()}"
            file_path = os.path.join(tempfile.gettempdir(), file_name)

            try:
                if file_format.lower() == "csv":
                    with open(file_path, "w", newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        aircraft_keys = list(response['aircraft'][0].keys())
                        writer.writerow([key.upper() for key in aircraft_keys])
                        for aircraft in response['aircraft']:
                            aircraft_values = list(map(str, aircraft.values()))
                            writer.writerow(aircraft_values)
                elif file_format.lower() == "pdf":
                    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4)) 
                    styles = getSampleStyleSheet()
                    styles.add(ParagraphStyle(name='Normal-Bold', fontName='Helvetica-Bold', fontSize=14, leading=16, alignment=1)) 
                    flowables = []

                    flowables.append(Paragraph(f"<u>{search_type.capitalize()} {search_value}</u>", styles['Normal-Bold'])) 
                    flowables.append(Spacer(1, 24)) 

                    aircraft_keys = list(response['aircraft'][0].keys())
                    data = [Paragraph(f"<b>{key}</b>", styles['Normal-Bold']) for key in aircraft_keys]
                    flowables.extend(data)

                    for aircraft in response['aircraft']:
                        aircraft_values = list(map(str, aircraft.values()))
                        data = [Paragraph(value, styles['Normal']) for value in aircraft_values]
                        flowables.extend(data)
                        flowables.append(PageBreak())

                    doc.build(flowables)
                elif file_format.lower() in ["txt"]:
                    with open(file_path, "w", newline='', encoding='utf-8') as file:
                        aircraft_keys = list(response['aircraft'][0].keys())
                        file.write(' '.join([key.upper() for key in aircraft_keys]) + '\n')
                        for aircraft in response['aircraft']:
                            aircraft_values = list(map(str, aircraft.values()))
                            file.write(' '.join(aircraft_values) + '\n')
                elif file_format.lower() == "html":
                    with open(file_path, "w", newline='', encoding='utf-8') as file:
                        aircraft_keys = list(response['aircraft'][0].keys())
                        file.write('<table>\n')
                        file.write('<tr>\n')
                        for key in aircraft_keys:
                            file.write(f'<th>{key.upper()}</th>\n')
                        file.write('</tr>\n')
                        for aircraft in response['aircraft']:
                            aircraft_values = list(map(str, aircraft.values()))
                            file.write('<tr>\n')
                            for value in aircraft_values:
                                file.write(f'<td>{value}</td>\n')
                            file.write('</tr>\n')
                        file.write('</table>\n')
            except PermissionError as e:
                embed = discord.Embed(title="Error", description="I do not have permission to write to the file system.", color=0xff4545)
                await ctx.send(embed=embed)
                if os.path.exists(file_path):
                    os.remove(file_path)

            with open(file_path, 'rb') as fp:
                await ctx.send(file=discord.File(fp, filename=os.path.basename(file_path)))
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)


    @commands.guild_only()
    @aircraft_group.command(name='scroll', help='Scroll through available planes.')
    async def scroll_planes(self, ctx):
        # Use new REST API endpoint for military aircraft - must combine with base query
        url = f"{self.api_url}/?all_with_pos&filter_mil"
        try:
            response = await self._make_request(url, ctx)
            if response and 'aircraft' in response:
                for index, aircraft_info in enumerate(response['aircraft']):
                    await self._send_aircraft_info(ctx, {'aircraft': [aircraft_info]})
                    embed = discord.Embed(description=f"Plane {index + 1}/{len(response['aircraft'])}. React with ➡️ to view the next plane or ⏹️ to stop.")
                    message = await ctx.send(embed=embed)
                    await message.add_reaction("➡️")
                    await message.add_reaction("⏹️") 

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) == '➡️' or str(reaction.emoji) == '⏹️'

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        await message.remove_reaction(reaction.emoji, ctx.author)
                        if str(reaction.emoji) == '⏹️':
                            embed = discord.Embed(description="Stopping.")
                            await ctx.send(embed=embed)
                            break
                    except asyncio.TimeoutError:
                        embed = discord.Embed(description="No reaction received. Stopping.")
                        await ctx.send(embed=embed)
                        break
        except Exception as e:
            embed = discord.Embed(description=f"An error occurred during scrolling: {e}.")
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='showalertchannel', help='Show alert task status and output if set')
    async def list_alert_channels(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"Squawk alerts for {guild.name}", color=0xfffffe)
        alert_channel_id = await self.config.guild(guild).alert_channel()
        if alert_channel_id:
            alert_channel = self.bot.get_channel(alert_channel_id)
            if alert_channel:
                next_iteration = self.check_emergency_squawks.next_iteration
                now = datetime.datetime.now(datetime.timezone.utc)
                if next_iteration:
                    time_remaining = (next_iteration - now).total_seconds()
                    if time_remaining > 0: 
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                else:
                    time_remaining = self.check_emergency_squawks.seconds
                    if time_remaining > 0:
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                if self.check_emergency_squawks.is_running():
                    last_check_status = f":white_check_mark: **Checked successfully, next checking {time_remaining_formatted}**"
                else:
                    last_check_status = f":x: **Last check failed, retrying {time_remaining_formatted}**"
                embed.add_field(name="Status", value=f"Channel: {alert_channel.mention}\nLast check: {last_check_status}", inline=False)
                
                last_emergency_squawk_time = await self.config.guild(guild).last_emergency_squawk_time()
                if last_emergency_squawk_time:
                    last_emergency_squawk_time_formatted = f"<t:{int(last_emergency_squawk_time)}:F>"
                    embed.add_field(name="Last Emergency Squawk", value=f"Time: {last_emergency_squawk_time_formatted}", inline=False)
                else:
                    embed.add_field(name="Last Emergency Squawk", value="No emergency squawks yet.", inline=False)
            else:
                embed.add_field(name="Status", value="No alert channel set.", inline=False)
        else:
            embed.add_field(name="Status", value="No alert channel set.", inline=False)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.admin_or_permissions()
    @aircraft_group.command(name='alertchannel', help='Set or clear a channel to send emergency squawk alerts to. Clear with no channel.')
    async def set_alert_channel(self, ctx, channel: discord.TextChannel = None):
        if channel:
            try:
                await self.config.guild(ctx.guild).alert_channel.set(channel.id)
                embed = discord.Embed(description=f"Alert channel set to {channel.mention}", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error setting alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            try:
                await self.config.guild(ctx.guild).alert_channel.clear()
                embed = discord.Embed(description="Alert channel cleared. No more alerts will be sent.", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error clearing alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)
    
    @commands.guild_only()
    @commands.admin_or_permissions()
    @aircraft_group.command(name='alertrole', help='Set or clear a role to mention when new emergency squawks occur. Clear with no role.')
    async def set_alert_role(self, ctx, role: discord.Role = None):
        if role:
            try:
                await self.config.guild(ctx.guild).alert_role.set(role.id)
                embed = discord.Embed(description=f"Alert role set to {role.mention}", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error setting alert role: {e}", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            try:
                await self.config.guild(ctx.guild).alert_role.clear()
                embed = discord.Embed(description="Alert role cleared. No more role mentions will be made.", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error clearing alert role: {e}", color=0xff4545)
                await ctx.send(embed=embed)


    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @aircraft_group.command(name='autoicao')
    async def autoicao(self, ctx, state: bool = None):
        """Enable or disable automatic ICAO lookup."""
        if state is None:
            state = await self.config.guild(ctx.guild).auto_icao()
            if state:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup is currently enabled.", color=0x2BBD8E)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup is currently disabled.", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            await self.config.guild(ctx.guild).auto_icao.set(state)
            if state:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup has been enabled.", color=0x2BBD8E)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup has been disabled.", color=0xff4545)
                await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.group(name='airport', help='Command center for airport related commands')
    async def airport_group(self, ctx):
         """Command center for airport related commands"""

    @commands.guild_only()
    @airport_group.command(name='info')
    async def airportinfo(self, ctx, code: str = None):
        """Query airport information by ICAO or IATA code."""
        if code is None:
            embed = discord.Embed(title="Error", description="Please provide an ICAO or IATA code.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        # Determine if the code is ICAO or IATA based on length
        if len(code) == 4:
            code_type = 'icao'
        elif len(code) == 3:
            code_type = 'iata'
        else:
            embed = discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        try:
            async with ctx.typing():
                url1 = f"https://airport-data.com/api/ap_info.json?{code_type}={code}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url1) as response1:
                        data1 = await response1.json()
                
                if 'error' in data1 or not data1 or 'name' not in data1:
                    embed = discord.Embed(title="Error", description="No airport found with the provided code.", color=0xff4545)
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(title=f"{data1.get('name', 'Unknown Airport')}", color=0xfffffe)

                # Check for OpenAI API key and use it to generate a summary if available
                openai_api_key = await self.bot.get_shared_api_tokens("openai")
                if openai_api_key and 'api_key' in openai_api_key:
                    openai_api_key = openai_api_key['api_key']
                    airport_name = data1.get('name', 'Unknown Airport')
                    openai_payload = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an AI summarizer inside a Discord bot feature. Produce text without titles or headings, and use markdown for styling like - bulletpoints where appropriate. Don't mention terrorist attacks or other world terrorism events. Don't mention the airport's name, ICAO or IATA."
                            },
                            {
                                "role": "user",
                                "content": f"Generate a summary of the airport named {airport_name}. Include 3 links as bulletpoints where I can read more about the airport"
                            }
                        ]
                    }
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {openai_api_key}"
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=openai_payload) as openai_response:
                            if openai_response.status == 200:
                                openai_data = await openai_response.json()
                                summary = openai_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                                embed.description = summary
                                embed.set_footer(text="Summary generated using AI, check factual accuracy")

                googlemaps_tokens = await self.bot.get_shared_api_tokens("googlemaps")
                google_street_view_api_key = googlemaps_tokens.get("api_key", "YOUR_API_KEY")
                
                file = None  # Initialize file to None to handle cases where no image is available
                if google_street_view_api_key != "YOUR_API_KEY":
                    street_view_base_url = "https://maps.googleapis.com/maps/api/staticmap"
                    street_view_params = {
                        "size": "1920x1080", # Width x Height
                        "zoom": "12",
                        "scale": "2", 
                        "center": f"{data1['latitude']},{data1['longitude']}",  # Latitude and Longitude as comma-separated string
                        "maptype": "hybrid",
                        "key": google_street_view_api_key
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.get(street_view_base_url, params=street_view_params) as street_view_response:
                            if street_view_response.status == 200:
                                # Save the raw binary that the API returns as an image to set in embed.set_image
                                street_view_image_url = "attachment://street_view_image.png"
                                embed.set_image(url=street_view_image_url)
                                street_view_image_stream = io.BytesIO(await street_view_response.read())
                                file = discord.File(fp=street_view_image_stream, filename="street_view_image.png")
                            else:
                                # Handle the error accordingly, e.g., log it or send a message to the user
                                pass

                view = discord.ui.View(timeout=180)  # Initialize view outside of the else block
                if 'icao' in data1:
                    embed.add_field(name='ICAO', value=f"{data1['icao']}", inline=True)
                if 'iata' in data1:
                    embed.add_field(name='IATA', value=f"{data1['iata']}", inline=True)
                if 'country_code' in data1:
                    embed.add_field(name='Country code', value=f":flag_{data1['country_code'].lower()}: {data1['country_code']}", inline=True)
                if 'location' in data1:
                    embed.add_field(name='Location', value=f"{data1['location']}", inline=True)
                if 'country' in data1:
                    embed.add_field(name='Country', value=f"{data1['country']}", inline=True)
                if 'longitude' in data1:
                    embed.add_field(name='Longitude', value=f"{data1['longitude']}", inline=True)
                if 'latitude' in data1:
                    embed.add_field(name='Latitude', value=f"{data1['latitude']}", inline=True)
                
                # Check if 'link' is in data1 and add it to the view
                if 'link' in data1:
                    link = data1['link']
                    if not (link.startswith('http://') or link.startswith('https://')):
                        link = 'https://airport-data.com' + link
                    # URL button
                    view_airport = discord.ui.Button(label=f"More info about {data1['icao']}", url=link, style=discord.ButtonStyle.link)
                    view.add_item(view_airport)

            # Send the message with the embed, view, and file (if available)
            await ctx.send(embed=embed, view=view, file=file)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @airport_group.command(name='runway')
    async def runwayinfo(self, ctx, code: str):
        """Query runway information by ICAO code."""
        if len(code) != 4:
            if len(code) == 3:
                code_type = 'iata'
            else:
                embed = discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545)
                await ctx.send(embed=embed)
                return
        else:
            code_type = 'icao'

        try:
            if code_type == 'iata':
                url1 = f"https://airport-data.com/api/ap_info.json?iata={code}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url1) as response1:
                        data1 = await response1.json()
                        if 'icao' in data1:
                            code = data1['icao']
                        else:
                            embed = discord.Embed(title="Error", description="No ICAO code found for the provided IATA code.", color=0xff4545)
                            await ctx.send(embed=embed)
                            return

            api_token = await self.bot.get_shared_api_tokens("airportdbio")
            if api_token and 'api_token' in api_token:
                url2 = f"https://airportdb.io/api/v1/airport/{code}?apiToken={api_token['api_token']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url2) as response2:
                        data2 = await response2.json()

                if 'error' in data2:
                    error_message = data2['error']
                    if len(error_message) > 1024:
                        error_message = error_message[:1021] + "..."
                    embed = discord.Embed(title="Error", description=error_message, color=0xff4545)
                    await ctx.send(embed=embed)
                elif not data2 or 'name' not in data2:
                    embed = discord.Embed(title="Error", description="No airport found with the provided code.", color=0xff4545)
                    await ctx.send(embed=embed)
                else:
                    combined_pages = []
                    if 'runways' in data2:
                        embed = discord.Embed(title=f"Runway information for {code.upper()}", color=0xfffffe)
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/layers.png")
                        runways = data2['runways']
                        for runway in runways:
                            if 'id' in runway:
                                embed.add_field(name="Runway ID", value=f"**`{runway['id']}`**", inline=True)

                            if 'surface' in runway:
                                embed.add_field(name="Surface", value=f"**`{runway['surface']}`**", inline=True)

                            if 'length_ft' in runway and 'width_ft' in runway:
                                embed.add_field(name="Dimensions", value=f"**`{runway['length_ft']}ft long`\n`{runway['width_ft']}ft wide`**", inline=True)

                            if 'le_ident' in runway or 'he_ident' in runway:
                                ils_value = ""
                                if 'le_ident' in runway:
                                    ils_info = runway.get('le_ils', {})
                                    ils_freq = ils_info.get('freq', 'N/A')
                                    ils_course = ils_info.get('course', 'N/A')
                                    ils_value += f"**{runway['le_ident']}** *`{ils_freq} MHz @ {ils_course}°`*\n"
                                if 'he_ident' in runway:
                                    ils_info = runway.get('he_ils', {})
                                    ils_freq = ils_info.get('freq', 'N/A')
                                    ils_course = ils_info.get('course', 'N/A')
                                    ils_value += f"**{runway['he_ident']}** *`{ils_freq} MHz @ {ils_course}°`*\n"
                                embed.add_field(name="Landing assistance", value=ils_value.strip(), inline=True)

                            runway_status = ":white_check_mark: **`Open`**" if str(runway.get('closed', 0)) == '0' else ":x: **`Closed`**"
                            embed.add_field(name="Runway status", value=runway_status, inline=True)

                            lighted_status = ":bulb: **`Lighted`**" if str(runway.get('lighted', 0)) == '1' else ":x: **`Not Lighted`**"
                            embed.add_field(name="Lighting", value=lighted_status, inline=True)

                            combined_pages.append(embed)
                            embed = discord.Embed(title=f"Runway information for {code.upper()}", color=0xfffffe)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/layers.png")

                    await self.paginate_embed(ctx, combined_pages)
            else:
                embed = discord.Embed(title="Error", description="API token for airportdb.io not configured.", color=0xff4545)
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    async def paginate_embed(self, ctx, pages):
        message = await ctx.send(embed=pages[0])
        await message.add_reaction("⬅️")
        await message.add_reaction("❌")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "❌", "➡️"]

        i = 0
        reaction = None
        while True:
            if str(reaction) == "⬅️":
                if i > 0:
                    i -= 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == "➡️":
                if i < len(pages) - 1:
                    i += 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == "❌":
                await message.delete()
                break
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                await asyncio.sleep(1)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    @commands.guild_only()
    @airport_group.command(name='navaid')
    async def navaidinfo(self, ctx, code: str):
        """Query navaid information by ICAO code."""
        if len(code) != 4:
            if len(code) == 3:
                code_type = 'iata'
            else:
                embed = discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545)
                await ctx.send(embed=embed)
                return
        else:
            code_type = 'icao'

        try:
            if code_type == 'iata':
                url1 = f"https://airport-data.com/api/ap_info.json?iata={code}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url1) as response1:
                        data1 = await response1.json()
                        if 'icao' in data1:
                            code = data1['icao']
                        else:
                            embed = discord.Embed(title="Error", description="No ICAO code found for the provided IATA code.", color=0xff4545)
                            await ctx.send(embed=embed)
                            return

            api_token = await self.bot.get_shared_api_tokens("airportdbio")
            if api_token and 'api_token' in api_token:
                url = f"https://airportdb.io/api/v1/airport/{code}?apiToken={api_token['api_token']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        data = await response.json()

                if 'error' in data:
                    error_message = data['error']
                    if len(error_message) > 1024:
                        error_message = error_message[:1021] + "..."
                    embed = discord.Embed(title="Error", description=error_message, color=0xff4545)
                    await ctx.send(embed=embed)
                elif not data or 'name' not in data:
                    embed = discord.Embed(title="Error", description="No airport found with the provided code.", color=0xff4545)
                    await ctx.send(embed=embed)
                else:
                    combined_pages = []
                    if 'navaids' in data:
                        embed = discord.Embed(title=f"Navigational aids at {code.upper()}", color=0xfffffe)
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/navigate.png")
                        navaids = data['navaids']
                        for navaid in navaids:
                            if 'ident' in navaid and navaid['ident']:
                                embed.add_field(name="Ident", value=f"**`{navaid['ident']}`**", inline=True)

                            if 'name' in navaid and navaid['name']:
                                embed.add_field(name="Name", value=f"**`{navaid['name']}`**", inline=True)

                            if 'type' in navaid and navaid['type']:
                                embed.add_field(name="Type", value=f"**`{navaid['type']}`**", inline=True)

                            if 'frequency_khz' in navaid and navaid['frequency_khz']:
                                embed.add_field(name="Frequency", value=f"**`{navaid['frequency_khz']}khz`**", inline=True)

                            if 'latitude_deg' in navaid and 'longitude_deg' in navaid and navaid['latitude_deg'] and navaid['longitude_deg']:
                                latitude = "{:.6f}".format(float(navaid['latitude_deg']))
                                longitude = "{:.6f}".format(float(navaid['longitude_deg']))
                                embed.add_field(name="Coordinates", value="**`{}°, {}°`**".format(latitude, longitude), inline=True)

                            if 'elevation_ft' in navaid and navaid['elevation_ft']:
                                embed.add_field(name="Elevation", value=f"**`{navaid['elevation_ft']}ft`**", inline=True)

                            if 'usageType' in navaid and navaid['usageType']:
                                embed.add_field(name="Usage", value=f"**`{navaid['usageType']}`**", inline=True)

                            if 'power' in navaid and navaid['power']:
                                embed.add_field(name="Signal power", value=f"**`{navaid['power']}`**", inline=True)

                            if 'associated_airport' in navaid and navaid['associated_airport']:
                                embed.add_field(name="Airport", value=f"**`{navaid['associated_airport']}`**", inline=True)

                            combined_pages.append(embed)
                            embed = discord.Embed(title=f"Navaid information for {code.upper()}", color=0xfffffe)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/navigate.png")

                    await self.paginate_embed(ctx, combined_pages)
            else:
                embed = discord.Embed(title="Error", description="API token for airportdb.io not configured.", color=0xff4545)
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @airport_group.command(name='forecast', help='Get the weather for an airport by ICAO or IATA code.')
    async def get_forecast(self, ctx, code: str):
        """Fetch the latitude and longitude of an airport via IATA or ICAO code, then show the forecast"""
        code_type = 'icao' if len(code) == 4 else 'iata' if len(code) == 3 else None
        if not code_type:
            await ctx.send(embed=discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545))
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://airport-data.com/api/ap_info.json?{code_type}={code}") as response1:
                    data1 = await response1.json()
                    latitude, longitude = data1.get('latitude'), data1.get('longitude')
                    if not latitude or not longitude:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch latitude and longitude for the provided code.", color=0xff4545))
                        return
                    if data1.get('country_code') != 'US':
                        await ctx.send(embed=discord.Embed(title="Error", description="Weather forecasts are currently only available for airports in the United States.", color=0xff4545))
                        return

                async with session.get(f"https://api.weather.gov/points/{latitude},{longitude}") as response2:
                    data2 = await response2.json()
                    forecast_url = data2.get('properties', {}).get('forecast')
                    if not forecast_url:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast URL.", color=0xff4545))
                        return

                async with session.get(forecast_url) as response3:
                    data3 = await response3.json()
                    periods = data3.get('properties', {}).get('periods')
                    if not periods:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast details.", color=0xff4545))
                        return

            combined_pages = []
            
            for period in periods:
                timeemoji = "☀️" if period.get('isDaytime') else "🌙"
                description = f" # {timeemoji} {period['name']}"
                embed = discord.Embed(title=f"Weather forecast for {code.upper()}", description=description, color=0xfffffe)

                temperature = period['temperature']
                temperature_unit = period['temperatureUnit']
                
                # Determine the emoji based on temperature
                if temperature_unit == 'F':
                    if temperature >= 90:
                        emoji = '🔥'  # Hot
                    elif temperature <= 32:
                        emoji = '❄️'  # Cold
                    else:
                        emoji = '🌡️'  # Moderate
                else:  # Assuming Celsius
                    if temperature >= 32:
                        emoji = '🔥'  # Hot
                    elif temperature <= 0:
                        emoji = '❄️'  # Cold
                    else:
                        emoji = '🌡️'  # Moderate

                embed.add_field(name="Temperature", value=f"{emoji} **`{temperature}° {temperature_unit}`**", inline=True)

                wind_speed = period['windSpeed']
                wind_direction = period['windDirection']

                # Determine the emoji based on wind speed
                try:
                    speed_value = int(wind_speed.split()[0])
                    if speed_value >= 30:
                        wind_emoji = '💨'  # Strong wind
                    elif speed_value >= 15:
                        wind_emoji = '🌬️'  # Moderate wind
                    else:
                        wind_emoji = '🍃'  # Light wind
                except ValueError:
                    wind_emoji = '🍃'  # Default to light wind if parsing fails

                # Determine the emoji based on wind direction
                direction_emoji = {
                    'N': '⬆️',
                    'NNE': '⬆️↗️',
                    'NE': '↗️',
                    'ENE': '↗️➡️',
                    'E': '➡️',
                    'ESE': '➡️↘️',
                    'SE': '↘️',
                    'SSE': '↘️⬇️',
                    'S': '⬇️',
                    'SSW': '⬇️↙️',
                    'SW': '↙️',
                    'WSW': '↙️⬅️',
                    'W': '⬅️',
                    'WNW': '⬅️↖️',
                    'NW': '↖️',
                    'NNW': '↖️⬆️'
                }.get(wind_direction, '❓')  # Default to question mark if direction is unknown
                embed.add_field(name="Wind speed", value=f"{wind_emoji} **`{wind_speed}`**", inline=True)
                embed.add_field(name="Wind direction", value=f"{direction_emoji} **`{wind_direction}`**", inline=True)
                
                if 'relativeHumidity' in period and period['relativeHumidity']['value'] is not None:
                    embed.add_field(name="Humidity", value=f"**`{period['relativeHumidity']['value']}%`**", inline=True)

                if 'probabilityOfPrecipitation' in period and period['probabilityOfPrecipitation']['value'] is not None:
                    embed.add_field(name="Chance of precipitation", value=f"**`{period['probabilityOfPrecipitation']['value']}%`**", inline=True)
                    
                if 'dewpoint' in period and period['dewpoint']['value'] is not None:
                    dewpoint_celsius = period['dewpoint']['value']
                    dewpoint_fahrenheit = (dewpoint_celsius * 9/5) + 32
                    embed.add_field(name="Dewpoint", value=f"**`{dewpoint_fahrenheit:.1f}°F`**", inline=True)
                embed.add_field(name="Forecast", value=f"**`{period['detailedForecast']}`**", inline=False)

                combined_pages.append(embed)

            await self.paginate_embed(ctx, combined_pages)

        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Error", description=str(e), color=0xff4545))



    @tasks.loop(minutes=2)
    async def check_emergency_squawks(self):
        try:
            emergency_squawk_codes = ['7500', '7600', '7700']
            for squawk_code in emergency_squawk_codes:
                # Use new REST API endpoint for squawk filter - must combine with base query
                url = f"{self.api_url}/?all_with_pos&filter_squawk={squawk_code}"
                response = await self._make_request(url)  # No ctx for background task
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
                                    await self._send_aircraft_info(alert_channel, {'aircraft': [aircraft_info]})
                                    
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
        await self.bot.wait_until_ready()  # Removed unnecessary try-except block

    @commands.Cog.listener()
    async def on_message(self, message):
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
            await self.aircraft_by_icao(ctx, content)

    def cog_unload(self):
        try:
            self.check_emergency_squawks.cancel()
        except Exception as e:
            print(f"Error unloading cog: {e}")

    @commands.is_owner()
    @commands.command(name='setapikey', help='Set the API key for Skysearch.')
    async def set_api_key(self, ctx, api_key: str):
        """Command to set the API key."""
        await self.config.airplanesliveapi.set(api_key)
        embed = discord.Embed(title="API Key Updated", description="The airplanes.live API key has been set successfully.", color=0x2BBD8E)
        embed.add_field(name="Status", value="✅ API key configured", inline=True)
        embed.add_field(name="Header", value="`auth: [your-api-key]`", inline=True)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name='apikey', help='Check the status of the API key configuration.')
    async def check_api_key(self, ctx):
        """Command to check API key status."""
        api_key = await self.config.airplanesliveapi()
        if api_key:
            embed = discord.Embed(title="API Key Status", description="✅ API key is configured", color=0x2BBD8E)
            embed.add_field(name="Status", value="Configured", inline=True)
            embed.add_field(name="Key Preview", value=f"`{api_key[:8]}...`", inline=True)
            embed.add_field(name="Header Format", value="`auth: [your-api-key]`", inline=True)
        else:
            embed = discord.Embed(title="API Key Status", description="❌ No API key configured", color=0xff4545)
            embed.add_field(name="Status", value="Not configured", inline=True)
            embed.add_field(name="Usage", value="Use `setapikey <your-api-key>` to configure", inline=True)
            embed.add_field(name="Note", value="Some features may be limited without an API key", inline=True)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name='clearapikey', help='Clear the API key configuration.')
    async def clear_api_key(self, ctx):
        """Command to clear the API key."""
        await self.config.airplanesliveapi.clear()
        embed = discord.Embed(title="API Key Cleared", description="The airplanes.live API key has been cleared.", color=0xff4545)
        embed.add_field(name="Status", value="❌ API key removed", inline=True)
        embed.add_field(name="Note", value="Some features may be limited without an API key", inline=True)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name='debugapi', help='Debug API key and connection issues (DM only)')
    async def debug_api(self, ctx):
        """Debug API key and connection issues - sends detailed info via DM."""
        try:
            # Check if we can DM the user
            try:
                await ctx.author.send("🔧 **airplanes.live API Debug Test**\n\nStarting comprehensive API diagnostics...")
            except discord.Forbidden:
                await ctx.send("❌ **Error:** I cannot send you a DM. Please enable DMs from server members and try again.")
                return

            # Get API key status
            api_key = await self.config.airplanesliveapi()
            debug_info = f"**API Key Status:**\n"
            if api_key:
                debug_info += f"✅ **Configured:** `{api_key[:8]}...`\n"
                debug_info += f"📏 **Length:** {len(api_key)} characters\n"
            else:
                debug_info += f"❌ **Not configured**\n"
            
            debug_info += f"\n**Headers being sent:**\n"
            headers = await self._get_headers()
            debug_info += f"```{headers}```\n"

            # Test basic connectivity
            debug_info += f"**Testing basic connectivity...**\n"
            try:
                if not hasattr(self, '_http_client'):
                    self._http_client = aiohttp.ClientSession()
                
                # Test without API key first
                test_url = f"{self.api_url}/?all_with_pos"
                debug_info += f"🔗 **Test URL:** `{test_url}`\n"
                
                async with self._http_client.get(test_url) as response:
                    debug_info += f"📡 **Response Status:** {response.status}\n"
                    debug_info += f"📋 **Response Headers:** `{dict(response.headers)}`\n"
                    
                    if response.status == 200:
                        debug_info += f"✅ **Basic connectivity:** Working\n"
                    else:
                        debug_info += f"❌ **Basic connectivity:** Failed (Status {response.status})\n"
                        
            except Exception as e:
                debug_info += f"❌ **Connectivity Error:** {str(e)}\n"

            # Test with API key if available
            if api_key:
                debug_info += f"\n**Testing with API key...**\n"
                try:
                    test_url_with_key = f"{self.api_url}/?all_with_pos"
                    async with self._http_client.get(test_url_with_key, headers=headers) as response:
                        debug_info += f"📡 **Authenticated Status:** {response.status}\n"
                        
                        if response.status == 200:
                            debug_info += f"✅ **Authentication:** Working\n"
                            try:
                                data = await response.json()
                                debug_info += f"📊 **Response Keys:** `{list(data.keys())}`\n"
                                if 'aircraft' in data:
                                    debug_info += f"✈️ **Aircraft Count:** {len(data['aircraft'])} aircraft\n"
                                debug_info += f"⏱️ **Response Time:** {response.headers.get('X-RateLimit-Remaining', 'Unknown')} requests remaining\n"
                            except Exception as e:
                                debug_info += f"❌ **JSON Parse Error:** {str(e)}\n"
                        elif response.status == 401:
                            debug_info += f"❌ **Authentication:** Failed - Invalid API key\n"
                        elif response.status == 403:
                            debug_info += f"❌ **Authentication:** Failed - Insufficient permissions\n"
                        elif response.status == 429:
                            debug_info += f"❌ **Rate Limit:** Exceeded\n"
                        else:
                            debug_info += f"❌ **Authentication:** Failed - Status {response.status}\n"
                            
                except Exception as e:
                    debug_info += f"❌ **API Test Error:** {str(e)}\n"

            # Test specific endpoints
            debug_info += f"\n**Testing specific endpoints...**\n"
            test_endpoints = [
                ("Military aircraft", f"{self.api_url}/?all_with_pos&filter_mil"),
                ("LADD aircraft", f"{self.api_url}/?all_with_pos&filter_ladd"),
                ("PIA aircraft", f"{self.api_url}/?all_with_pos&filter_pia"),
                ("Emergency squawk 7700", f"{self.api_url}/?all_with_pos&filter_squawk=7700")
            ]
            
            for endpoint_name, endpoint_url in test_endpoints:
                try:
                    async with self._http_client.get(endpoint_url, headers=headers) as response:
                        debug_info += f"🔗 **{endpoint_name}:** Status {response.status}\n"
                        if response.status == 200:
                            try:
                                data = await response.json()
                                if 'aircraft' in data:
                                    debug_info += f"   ✈️ Found {len(data['aircraft'])} aircraft\n"
                            except:
                                pass
                except Exception as e:
                    debug_info += f"❌ **{endpoint_name}:** Error - {str(e)}\n"

            # Final summary
            debug_info += f"\n**📋 Summary:**\n"
            debug_info += f"• **API Base URL:** `{self.api_url}`\n"
            debug_info += f"• **API Key:** {'✅ Configured' if api_key else '❌ Not configured'}\n"
            debug_info += f"• **Session:** {'✅ Active' if hasattr(self, '_http_client') else '❌ Not initialized'}\n"
            
            # Send the debug info in chunks if it's too long
            if len(debug_info) > 2000:
                chunks = [debug_info[i:i+1900] for i in range(0, len(debug_info), 1900)]
                for i, chunk in enumerate(chunks):
                    await ctx.author.send(f"**Debug Info (Part {i+1}/{len(chunks)}):**\n```{chunk}```")
            else:
                await ctx.author.send(f"**Debug Info:**\n```{debug_info}```")

            await ctx.send("✅ **Debug complete!** Check your DMs for detailed information.")

        except Exception as e:
            try:
                await ctx.author.send(f"❌ **Debug Error:** {str(e)}")
            except:
                await ctx.send(f"❌ **Debug Error:** {str(e)}")
            await ctx.send("❌ **Debug failed!** Check your DMs for error details.")
        
        
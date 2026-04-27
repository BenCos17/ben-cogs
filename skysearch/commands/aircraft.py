"""
Aircraft commands for SkySearch cog
"""


import asyncio
import datetime
import json
import os
import logging
import discord
from discord.ext import commands, tasks
from redbot.core import commands as red_commands
from redbot.core.i18n import Translator, cog_i18n

from ..utils.api import APIManager
from ..utils.helpers import HelperUtils
from ..utils.export import ExportManager

log = logging.getLogger("red.skysearch")

# Internationalization
_ = Translator("Skysearch", __file__)


@cog_i18n(_)
class AircraftCommands:
    """Aircraft-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
        self.api = APIManager(cog)
        self.helpers = HelperUtils(cog)
        self.export = ExportManager(cog)
        self._debug_enabled = False  # Debug output toggle
    
    async def send_aircraft_info(self, ctx, response):
        """Send aircraft information as an embed."""
        # Support both 'aircraft' and 'ac' keys
        aircraft_list = response.get('aircraft') or response.get('ac')
        if aircraft_list:
            await ctx.typing()
            aircraft_data = aircraft_list[0]
            # Get photo for the aircraft using full aircraft data
            image_url, photographer = await self.helpers.get_photo_by_aircraft_data(aircraft_data)
            # Create embed
            embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
            # Create view with buttons including Add to Watchlist
            view = self.helpers.create_aircraft_view_with_watchlist(aircraft_data)

            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(title=_("No results found for your query"), color=discord.Colour(0xff4545))
            embed.add_field(name=_("Details"), value=_("No aircraft information found or the response format is incorrect."), inline=False)
            await ctx.send(embed=embed)

    async def set_debug(self, ctx, enabled: bool):
        self._debug_enabled = enabled
        await ctx.send(f"[DEBUG] Aircraft debug output {'enabled' if enabled else 'disabled'}.")

    async def _debug_api_info(self, ctx, url):
        if not self._debug_enabled:
            return
        # Only allow bot owners to see the API key
        is_owner = False
        try:
            is_owner = await ctx.bot.is_owner(ctx.author)
        except Exception:
            pass
        if is_owner:
            api_key = await self.cog.config.airplanesliveapi()
            if api_key:
                masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else api_key
            else:
                masked_key = '(not set)'
            await ctx.send(f"[DEBUG] Endpoint: `{url}`\n[DEBUG] API key: `{masked_key}`")

    async def debug_lookup(self, ctx, lookup_type: str, value: str):
        if not self._debug_enabled:
            await ctx.send("[DEBUG] Aircraft debug output is currently disabled. Use `*aircraft debugtoggle on` to enable.")
            return
        # Build the endpoint URL
        if lookup_type == 'icao':
            url = f"/?find_hex={value}"
        elif lookup_type == 'callsign':
            url = f"/?find_callsign={value}"
        elif lookup_type == 'reg':
            url = f"/?find_reg={value}"
        elif lookup_type == 'type':
            url = f"/?find_type={value}"
        elif lookup_type == 'squawk':
            url = f"/?all_with_pos&filter_squawk={value}"
        else:
            await ctx.send("Invalid lookup_type. Must be one of: icao, callsign, reg, type, squawk.")
            return
        # Print endpoint and masked API key
        await self._debug_api_info(ctx, url)
        try:
            import time
            start = time.monotonic()
            response = await self.api.make_request(url, ctx)
            elapsed = time.monotonic() - start
            import json
            if response:
                pretty = json.dumps(response, indent=2)[:1900]  # Truncate to stay under Discord's 2000 char limit and avoid errors
                await ctx.send(f"[DEBUG] Raw API response (truncated):\n```json\n{pretty}\n```\n⏱️ API Latency: {elapsed:.2f} seconds")
            else:
                await ctx.send(f"[DEBUG] No response or empty response from the API.\n⏱️ API Latency: {elapsed:.2f} seconds")
            # if hasattr(response, 'headers') and 'X-RateLimit-Remaining' in response.headers:
            #     await ctx.send(f"[DEBUG] Requests remaining: {response.headers['X-RateLimit-Remaining']}")
        except Exception as e:
            await ctx.send(f"[DEBUG] Exception occurred: {e}")

    async def aircraft_by_icao(self, ctx, hex_id: str):
        """Get aircraft information by ICAO hex code."""
        url = f"/?find_hex={hex_id}"
        await self._debug_api_info(ctx, url)
        response = await self.api.make_request(url, ctx)
        api_mode = await self.cog.config.api_mode()
        key = 'aircraft' if api_mode == 'primary' else 'ac'
        aircraft_list = response.get(key) if response else None
        if aircraft_list and len(aircraft_list) > 0:
            if len(aircraft_list) > 1:
                for aircraft_info in aircraft_list:
                    await self.send_aircraft_info(ctx, {key: [aircraft_info]})
            else:
                await self.send_aircraft_info(ctx, {key: aircraft_list})
        else:
            embed = discord.Embed(title=_("No results found for your query"), color=discord.Colour(0xff4545))
            embed.add_field(name=_("Details"), value=_("No aircraft information found or the response format is incorrect."), inline=False)
            await ctx.send(embed=embed)

    async def aircraft_by_callsign(self, ctx, callsign: str):
        """Get aircraft information by callsign."""
        url = f"/?find_callsign={callsign}"
        await self._debug_api_info(ctx, url)
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title=_("Error"), description=_("No aircraft found with the specified callsign."), color=0xff4545)
            await ctx.send(embed=embed)

    async def aircraft_by_reg(self, ctx, registration: str):
        """Get aircraft information by registration."""
        url = f"/?find_reg={registration}"
        await self._debug_api_info(ctx, url)
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title=_("Error"), description=_("Error retrieving aircraft information."), color=0xff4545)
            await ctx.send(embed=embed)

    async def aircraft_by_type(self, ctx, aircraft_type: str):
        """Get aircraft information by type."""
        url = f"/?find_type={aircraft_type}"
        await self._debug_api_info(ctx, url)
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title=_("Error"), description=_("Error retrieving aircraft information."), color=0xff4545)
            await ctx.send(embed=embed)

    async def aircraft_by_squawk(self, ctx, squawk_value: str):
        """Get aircraft information by squawk code."""
        url = f"/?all_with_pos&filter_squawk={squawk_value}"
        await self._debug_api_info(ctx, url)
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    async def export_aircraft(self, ctx, search_type: str, search_value: str, file_format: str):
        """Export aircraft data to various formats."""
        # Map search_type to new REST API query parameters
        if search_type not in ["icao", "callsign", "squawk", "type"]:
            embed = discord.Embed(title=_("Error"), description=_("Invalid search type specified. Use one of: icao, callsign, squawk, or type."), color=0xfa4545)
            await ctx.send(embed=embed)
            return

        if file_format not in ["csv", "pdf", "txt", "html"]:
            embed = discord.Embed(title=_("Error"), description=_("Invalid file format specified. Use one of: csv, pdf, txt, or html."), color=0xfa4545)
            await ctx.send(embed=embed)
            return

        # Handle multiple ICAO codes for ICAO search type
        all_aircraft = []
        if search_type == "icao":
            # Split by spaces and clean up each ICAO code
            icao_codes = [code.strip() for code in search_value.split() if code.strip()]
            
            if not icao_codes:
                embed = discord.Embed(title=_("Error"), description=_("No valid ICAO codes provided."), color=0xfa4545)
                await ctx.send(embed=embed)
                return
            
            # Make separate API calls for each ICAO code
            for icao_code in icao_codes:
                url = f"/?find_hex={icao_code}"
                response = await self.api.make_request(url, ctx)
                if response and response.get('aircraft'):
                    all_aircraft.extend(response['aircraft'])
        else:
            # For other search types, use the original logic
            if search_type == "callsign":
                url = f"/?find_callsign={search_value}"
            elif search_type == "squawk":
                url = f"/?all_with_pos&filter_squawk={search_value}"
            elif search_type == "type":
                url = f"/?find_type={search_value}"
            else:
                embed = discord.Embed(title=_("Error"), description=_("Invalid search type specified."), color=0xfa4545)
                await ctx.send(embed=embed)
                return

            response = await self.api.make_request(url, ctx)
            if response and response.get('aircraft'):
                all_aircraft = response['aircraft']

        if not all_aircraft:
            embed = discord.Embed(title=_("Error"), description=_("No aircraft data found."), color=0xfa4545)
            await ctx.send(embed=embed)
            return

        # Export the data
        file_path, aircraft_count = await self.export.export_aircraft_data(
            all_aircraft, search_type, search_value, file_format, ctx
        )
        
        if file_path:
            with open(file_path, 'rb') as fp:
                # Create success embed showing export details
                embed = discord.Embed(title=_("Export Complete"), description=_("Successfully exported {count} aircraft to {format} format.").format(count=aircraft_count, format=file_format.upper()), color=0x2BBD8E)
                embed.add_field(name=_("Search Type"), value=search_type.capitalize(), inline=True)
                embed.add_field(name=_("Search Value"), value=search_value, inline=True)
                embed.add_field(name=_("File Format"), value=file_format.upper(), inline=True)
                embed.add_field(name=_("Aircraft Count"), value=f"{aircraft_count} aircraft", inline=True)
                embed.add_field(name=_("File Name"), value=os.path.basename(file_path), inline=True)
                
                await ctx.send(embed=embed, file=discord.File(fp, filename=os.path.basename(file_path)))
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    async def show_military_aircraft(self, ctx):
        """Get information about military aircraft."""
        url = f"/?all_with_pos&filter_mil"
        response = await self.api.make_request(url, ctx)
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

                    # Create temporary aircraft data for photo lookup
                    temp_aircraft_data = {'hex': aircraft_hex}
                    photo_url, photographer = await self.helpers.get_photo_by_aircraft_data(temp_aircraft_data)
                    if photo_url:
                        embed.set_image(url=photo_url)
                        if photographer:
                            embed.set_footer(text=f"Photo by {photographer}")
                    return embed

                async def update_message(message, page_index):
                    embed = await create_embed(aircraft_list[page_index])
                    await message.edit(embed=embed)

                embed = await create_embed(aircraft_list[page_index])
                message = await ctx.send(embed=embed)

                await message.add_reaction("⬅️")
                await message.add_reaction("❌")
                await message.add_reaction("➡️")
                
                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "❌", "➡️"]

                while True:
                    try:
                        reaction, user = await self.cog.bot.wait_for("reaction_add", timeout=60.0, check=check)

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
                await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    async def ladd_aircraft(self, ctx):
        """Get information on LADD-restricted aircraft."""
        url = f"/?all_with_pos&filter_ladd"
        response = await self.api.make_request(url, ctx)
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
                        reaction, user = await self.cog.bot.wait_for('reaction_add', timeout=60.0, check=check)
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
                await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    async def pia_aircraft(self, ctx):
        """View live aircraft using private ICAO addresses."""
        url = f"/?all_with_pos&filter_pia"
        response = await self.api.make_request(url, ctx)
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
                        reaction, user = await self.cog.bot.wait_for('reaction_add', timeout=60.0, check=check)
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
                await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    async def aircraft_within_radius(self, ctx, lat: str, lon: str, radius: str):
        """Get information about aircraft within a specified radius."""
        url = f"{await self.api.get_api_url()}/?circle={lat},{lon},{radius}"
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information for aircraft within the specified radius.", color=0xff4545)
            await ctx.send(embed=embed)

    async def closest_aircraft(self, ctx, lat: str, lon: str, radius: str = "100"):
        """Find the closest aircraft to specified coordinates."""
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
        url = f"{await self.api.get_api_url()}/?closest={lat},{lon},{radius}"
        response = await self.api.make_request(url, ctx)
        
        if response and 'aircraft' in response and response['aircraft']:
            aircraft_data = response['aircraft'][0]
            
            # Create a custom embed for closest aircraft with distance info
            embed = discord.Embed(title="Closest Aircraft Found", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            
            # Add distance information if available
            distance_nmi = aircraft_data.get('dst', 'Unknown')
            direction_deg = aircraft_data.get('dir', 'Unknown')
            
            if distance_nmi != 'Unknown' and direction_deg != 'Unknown':
                embed.description = _("**Distance:** {distance} nautical miles\n**Direction:** {direction}° from your location").format(distance=distance_nmi, direction=direction_deg)
            
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
            if icao and icao.upper() in self.cog.law_enforcement_icao_set:
                embed.add_field(name="Asset intelligence", value=":police_officer: Known for use by **state law enforcement**", inline=False)
            if icao and icao.upper() in self.cog.military_icao_set:
                embed.add_field(name="Asset intelligence", value=":military_helmet: Known for use in **military** and **government**", inline=False)
            if icao and icao.upper() in self.cog.medical_icao_set:
                embed.add_field(name="Asset intelligence", value=":hospital: Known for use in **medical response** and **transport**", inline=False)
            if icao and icao.upper() in self.cog.suspicious_icao_set:
                embed.add_field(name="Asset intelligence", value=":warning: Exhibits suspicious flight or **surveillance** activity", inline=False)
            if icao and icao.upper() in self.cog.global_prior_known_accident_set:
                embed.add_field(name="Asset intelligence", value=":boom: Prior involved in one or more **documented accidents**", inline=False)
            if icao and icao.upper() in self.cog.ukr_conflict_set:
                embed.add_field(name="Asset intelligence", value=":flag_ua: Utilized within the **[Russo-Ukrainian conflict](https://en.wikipedia.org/wiki/Russian-occupied_territories_of_Ukraine)**", inline=False)
            if icao and icao.upper() in self.cog.newsagency_icao_set:
                embed.add_field(name="Asset intelligence", value=":newspaper: Used by **news** or **media** organization", inline=False)
            if icao and icao.upper() in self.cog.balloons_icao_set:
                embed.add_field(name="Asset intelligence", value=":balloon: Aircraft is a **balloon**", inline=False)
            if icao and icao.upper() in self.cog.agri_utility_set:
                embed.add_field(name="Asset intelligence", value=":corn: Used for **agriculture surveys, easement validation, or land inspection**", inline=False)
            
            # Add photo if available
            temp_aircraft_data = {'hex': icao}
            image_url, photographer = await self.helpers.get_photo_by_aircraft_data(temp_aircraft_data)
            if image_url and photographer:
                embed.set_thumbnail(url=image_url)
                embed.set_footer(text=f"Photo by {photographer}")
            else:
                # Set default aircraft image when no photo is available
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                embed.set_footer(text="No photo available")
            
            # Create view with buttons including Add to Watchlist
            view = self.helpers.create_aircraft_view_with_watchlist(aircraft_data)
            
            await ctx.send(embed=embed, view=view)
            
        elif response and 'aircraft' in response and not response['aircraft']:
            embed = discord.Embed(title=_("No Aircraft Found"), description=_("No aircraft found within {radius} nautical miles of the specified location.").format(radius=radius), color=0xff4545)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=_("Error"), description=_("Error retrieving closest aircraft information."), color=0xff4545)
            await ctx.send(embed=embed)

    async def scroll_planes(self, ctx, category: str = 'mil'):
        """Scroll through available planes with button-based pagination. Category: mil, ladd, pia, all."""
        category = (category or 'mil').lower()
        if category == 'mil':
            url = f"/?all_with_pos&filter_mil"
        elif category == 'ladd':
            url = f"/?all_with_pos&filter_ladd"
        elif category == 'pia':
            url = f"/?all_with_pos&filter_pia"
        elif category == 'all':
            url = f"/?all_with_pos"
        else:
            url = f"/?all_with_pos&filter_mil"  # fallback to mil
        # Print the endpoint being used (before rewriting)
        await ctx.send(f"Using endpoint: `{url}` (will be rewritten if needed)")
        try:
            response = await self.api.make_request(url, ctx)
            # After make_request, print the final URL used (if possible)
            # (If you want to print the rewritten URL, you would need to modify APIManager to return it or log it.)
            if not response:
                embed = discord.Embed(title=_("Error"), description=_("No response from the API."), color=0xff4545)
                await ctx.send(embed=embed)
                return
            aircraft_list = response.get('aircraft') or response.get('ac')
            if not aircraft_list:
                embed = discord.Embed(title="No results found for your query", color=discord.Colour(0xff4545))
                embed.add_field(name="Details", value="No aircraft information found or the response format is incorrect.", inline=False)
                await ctx.send(embed=embed)
                return
            # Button-based pagination
            from discord.ui import View, Button

            class AircraftPaginator(View):
                def __init__(self, aircraft_list, parent, ctx):
                    super().__init__(timeout=120)
                    self.aircraft_list = aircraft_list
                    self.index = 0
                    self.parent = parent
                    self.ctx = ctx
                    self.message = None
                    self.update_buttons()
                def update_buttons(self):
                    self.clear_items()
                    self.add_item(Button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev", disabled=self.index == 0))
                    self.add_item(Button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next", disabled=self.index == len(self.aircraft_list) - 1))
                    self.add_item(Button(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop"))
                async def send_or_edit(self):
                    embed, view = await get_aircraft_embed_and_view(self.ctx, self.aircraft_list[self.index])
                    self.update_buttons()
                    if self.message:
                        await self.message.edit(embed=embed, view=self)
                    else:
                        self.message = await self.ctx.send(embed=embed, view=self)
                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    return interaction.user == self.ctx.author
                @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev", row=0)
                async def prev(self, interaction: discord.Interaction, button: Button):
                    if self.index > 0:
                        self.index -= 1
                        await self.send_or_edit()
                    await interaction.response.defer()
                @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next", row=0)
                async def next(self, interaction: discord.Interaction, button: Button):
                    if self.index < len(self.aircraft_list) - 1:
                        self.index += 1
                        await self.send_or_edit()
                    await interaction.response.defer()
                @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop", row=0)
                async def stop(self, interaction: discord.Interaction, button: Button):
                    await interaction.response.defer()
                    await self.message.edit(content="Pagination stopped.", embed=None, view=None)
                    self.stop()
            async def get_aircraft_embed_and_view(ctx, aircraft_info):
                icao_key = 'aircraft' if 'aircraft' in response else 'ac'
                return await self._get_aircraft_embed_and_view(ctx, {icao_key: [aircraft_info]})
            async def _get_aircraft_embed_and_view(self, ctx, response):
                aircraft_list = response.get('aircraft') or response.get('ac')
                if aircraft_list:
                    aircraft_data = aircraft_list[0]
                    image_url, photographer = await self.helpers.get_photo_by_aircraft_data(aircraft_data)
                    embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
                    view = self.helpers.create_aircraft_view_with_watchlist(aircraft_data)
                    return embed, view
                else:
                    embed = discord.Embed(title='No results found for your query', color=discord.Colour(0xff4545))
                    embed.add_field(name="Details", value="No aircraft information found or the response format is incorrect.", inline=False)
                    return embed, None
            self._get_aircraft_embed_and_view = _get_aircraft_embed_and_view.__get__(self)
            paginator = AircraftPaginator(aircraft_list, self, ctx)
            await paginator.send_or_edit()
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"Error scrolling through planes: {e}", color=0xff4545)
            await ctx.send(embed=embed)

    async def extract_feeder_url(self, ctx, *, json_input: str = None):
        """
        Extract feeder URL from JSON data or a URL containing feeder data.
        
        Args:
            json_input: Either a URL containing JSON data OR direct JSON text (optional)
        """
        if json_input:
            # Legacy support - if JSON input provided directly, parse it
            try:
                # Parse JSON input using utility function
                json_data = await self.helpers.parse_json_input(json_input)
                
                # Create embed using utility function
                embed = self.helpers.create_feeder_embed(json_data)
                
                # Create view using utility function
                view = self.helpers.create_feeder_view(json_input, json_data)
                
                await ctx.send(embed=embed, view=view)
                
            except ValueError as e:
                embed = discord.Embed(
                    title="Error", 
                    description=str(e), 
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                
            except Exception as e:
                embed = discord.Embed(
                    title="Error", 
                    description=f"Failed to extract feeder information: {str(e)}", 
                    color=0xff4545
                )
                await ctx.send(embed=embed)
        else:
            # Use modal for secure input
            embed = discord.Embed(
                title="Feeder JSON Parser", 
                description="Click the button below to securely input your JSON data using a text input modal.\n\n**Benefits:**\n• JSON data won't be visible in chat history\n• More secure than pasting in chat\n• Ephemeral response (only you can see it)\n• Supports both JSON text and URLs", 
                color=0x2BBD8E
            )
            from ..utils.helpers import JSONInputButton
            view = JSONInputButton(self.cog)
            await ctx.send(embed=embed, view=view)
    
    async def watchlist_add(self, ctx, item_type: str = None, *, value: str = None):
        """
        Add an item to the user's watchlist.
        
        REUSES: helpers.watchlist_add_item, helpers.normalize_watchlist
        
        Supports multiple watchlist types:
        - ICAO codes: aircraft by hex ID (6 hex digits)
        - Aircraft types: watch all military, medical, law_enforcement aircraft, etc.
        - Callsigns: watch specific flight numbers
        - Registrations: watch aircraft by tail number
        - Squawk codes: watch aircraft by squawk code
        
        Usage:
        - `watchlist add icao A2F41D` - Add by ICAO
        - `watchlist add type military` - Watch all military aircraft
        - `watchlist add callsign UNITED123` - Watch this callsign
        - `watchlist add reg N814AK` - Watch this registration
        - `watchlist add squawk 7700` - Watch aircraft squawking 7700
        """
        # Handle backward compatibility: if only one argument, auto-detect the type
        if item_type is not None and value is None:
            value = item_type.upper()
            # Auto-detect type based on format
            if value.isdigit() and len(value) == 4:
                item_type = 'squawk'  # 4 digits = squawk code
            elif all(c in '0123456789ABCDEFabcdef' for c in value) and len(value) == 6:
                item_type = 'icao'  # 6 hex chars = ICAO
            elif any(c.isalpha() for c in value) and value.replace('-', '').replace(' ', '').isalnum():
                # Has letters + optional dashes/spaces = registration or callsign
                # Check if it looks like a registration (usually short, with letter prefix)
                if len(value) <= 6 and value[0].isalpha():
                    item_type = 'reg'  # Likely a registration
                else:
                    item_type = 'callsign'  # Likely a callsign
            else:
                item_type = 'icao'  # Default fallback
        
        # Validate arguments
        if item_type is None or value is None:
            available_types = self.helpers.get_all_aircraft_type_names()
            embed = discord.Embed(
                title=_("Add to Watchlist"),
                description=_("Add aircraft or types to watch and get notified when they're active."),
                color=0xfffffe
            )
            embed.add_field(name=_("Usage"), value=_("`watchlist add <type> <value>`"), inline=False)
            embed.add_field(
                name=_("Types"),
                value=_("• `icao` - Aircraft by hex code (6 hex digits)\n• `type` - Watch aircraft category\n• `callsign` - Watch flight number\n• `reg` - Watch registration/tail number\n• `squawk` - Watch squawk code"),
                inline=False
            )
            embed.add_field(
                name=_("Aircraft types"),
                value=", ".join(available_types),
                inline=False
            )
            embed.add_field(
                name=_("Examples"),
                value=_("• `watchlist add icao A2F41D`\n• `watchlist add type military`\n• `watchlist add callsign UNITED123`\n• `watchlist add reg N814AK`\n• `watchlist add squawk 7700`"),
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        item_type = item_type.lower().strip()
        value = value.strip()
        
        # Validate item_type
        valid_types = ['icao', 'type', 'callsign', 'reg', 'squawk']
        if item_type not in valid_types:
            embed = discord.Embed(
                title=_("Invalid Type"),
                description=_("Type must be one of: {types}").format(types=", ".join(valid_types)),
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
        
        # Special validation for each type
        if item_type == 'icao':
            is_valid, error_msg = self.helpers.validate_icao(value)
            if not is_valid:
                embed = discord.Embed(
                    title=_("Invalid ICAO Code"),
                    description=error_msg,
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
        elif item_type == 'type':
            available_types = self.helpers.get_all_aircraft_type_names()
            if value.lower() not in available_types:
                embed = discord.Embed(
                    title=_("Invalid Aircraft Type"),
                    description=_("Unknown type: **{type}**\n\nAvailable types: {types}").format(
                        type=value,
                        types=", ".join(available_types)
                    ),
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
        elif item_type == 'squawk':
            # Validate squawk code (4 digits, octal)
            if not value.isdigit() or len(value) != 4:
                embed = discord.Embed(
                    title=_("Invalid Squawk Code"),
                    description=_("Squawk code must be 4 digits (e.g., 7700)."),
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
        
        # Add to watchlist using helper method
        user_config = self.cog.config.user(ctx.author)
        success, message = await self.helpers.watchlist_add_item(user_config, item_type, value)
        
        color = 0x00ff00 if success else 0xff4545
        embed = discord.Embed(
            title=_("✅ Watchlist Updated") if success else _("❌ Error"),
            description=message,
            color=color
        )
        await ctx.send(embed=embed)
    
    async def watchlist_remove(self, ctx, item_type: str = None, *, value: str = None):
        """
        Remove an item from the user's watchlist.
        
        REUSES: helpers.watchlist_remove_item, helpers.normalize_watchlist
        
        Same types as `watchlist add`:
        - icao, type, callsign, reg, squawk
        
        Usage:
        - `watchlist remove icao A2F41D`
        - `watchlist remove type military`
        - `watchlist remove callsign UNITED123`
        """
        # Handle backward compatibility
        if item_type is not None and value is None:
            value = item_type
            item_type = 'icao'
        
        if item_type is None or value is None:
            embed = discord.Embed(
                title=_("Remove from Watchlist"),
                description=_("Remove aircraft or types from your watchlist."),
                color=0xfffffe
            )
            embed.add_field(name=_("Usage"), value=_("`watchlist remove <type> <value>`"), inline=False)
            embed.add_field(
                name=_("Types"),
                value=_("• `icao` - Remove by aircraft hex code\n• `type` - Remove aircraft type\n• `callsign` - Remove by flight number\n• `reg` - Remove by registration\n• `squawk` - Remove by squawk code"),
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        item_type = item_type.lower().strip()
        value = value.strip()
        
        # Remove from watchlist using helper method
        user_config = self.cog.config.user(ctx.author)
        success, message = await self.helpers.watchlist_remove_item(user_config, item_type, value)
        
        color = 0x00ff00 if success else 0xff4545
        embed = discord.Embed(
            title=_("✅ Removed") if success else _("❌ Not Found"),
            description=message,
            color=color
        )
        await ctx.send(embed=embed)
    
    async def watchlist_list(self, ctx):
        """List all items in the user's watchlist (organized by type)."""
        user_config = self.cog.config.user(ctx.author)
        # Reuse normalize_watchlist and get_all_watchlist_items helpers
        watchlist = await self.helpers.get_all_watchlist_items(user_config)
        
        # Check if watchlist has any items
        total_items = sum(len(items) for items in watchlist.values() if isinstance(items, list))
        
        if total_items == 0:
            embed = discord.Embed(
                title=_("Watchlist Empty"),
                description=_("Your watchlist is empty.\n\nUse `{prefix}aircraft watchlist add <type> <value>` to add items.\n\nExample: `{prefix}aircraft watchlist add type military`").format(prefix=ctx.prefix),
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Create embed showing all watchlist items by type
        embed = discord.Embed(
            title=_("Your Watchlist"),
            description=_("You are watching **{count}** items:").format(count=total_items),
            color=0xfffffe
        )
        
        # Display each type that has items
        type_order = ['icao', 'type', 'callsign', 'reg', 'squawk']
        for item_type in type_order:
            items = watchlist.get(item_type, [])
            if items:
                # Format readable type name
                readable_type = self.helpers.get_readable_aircraft_type_name(item_type) if item_type == 'type' else item_type.upper()
                
                # Limit to 15 items per field to avoid embed limits
                display_items = items[:15]
                items_text = ", ".join([f"`{item}`" for item in display_items])
                
                if len(items) > 15:
                    items_text += f", ... and {len(items) - 15} more"
                
                embed.add_field(
                    name=f"{readable_type} ({len(items)})",
                    value=items_text or _("None"),
                    inline=False
                )
        
        embed.set_footer(text=_("Use `{prefix}aircraft watchlist status` for detailed status.").format(prefix=ctx.prefix))
        await ctx.send(embed=embed)
    
    async def watchlist_status(self, ctx):
        """Get status of watched aircraft and types."""
        user_config = self.cog.config.user(ctx.author)
        watchlist = await self.helpers.get_all_watchlist_items(user_config)
        
        total_items = sum(len(items) for items in watchlist.values() if isinstance(items, list))
        if total_items == 0:
            embed = discord.Embed(
                title=_("Watchlist Empty"),
                description=_("Your watchlist is empty."),
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        await ctx.typing()
        
        # Fetch all aircraft to check for matches
        try:
            url = f"{await self.cog.api.get_api_url()}/?all_with_pos"
            response = await self.cog.api.make_request(url, ctx)
            api_mode = await self.cog.config.api_mode()
            key = 'aircraft' if api_mode == 'primary' else 'ac'
            all_aircraft = response.get(key, []) if response else []
        except Exception as e:
            log.debug(f"Error fetching aircraft for watchlist status: {e}")
            all_aircraft = []
        
        # Check for matches
        matched_aircraft = []
        for aircraft_data in all_aircraft:
            if self.helpers.aircraft_matches_watchlist(aircraft_data, watchlist):
                matched_aircraft.append(aircraft_data)
        
        # Create status embed
        embed = discord.Embed(
            title=_("Watchlist Status"),
            description=_("**{total}** items in watchlist | **{online}** aircraft currently online").format(
                total=total_items,
                online=len(matched_aircraft)
            ),
            color=0xfffffe
        )
        
        # Show watched items
        type_order = ['icao', 'type', 'callsign', 'reg', 'squawk']
        for item_type in type_order:
            items = watchlist.get(item_type, [])
            if items:
                readable_type = self.helpers.get_readable_aircraft_type_name(item_type) if item_type == 'type' else item_type.upper()
                display_items = items[:10]
                items_text = ", ".join([f"`{item}`" for item in display_items])
                if len(items) > 10:
                    items_text += f", ... ({len(items) - 10} more)"
                
                embed.add_field(
                    name=readable_type,
                    value=items_text,
                    inline=False
                )
        
        # Show online matches (if any)
        if matched_aircraft:
            online_text = ""
            for aircraft in matched_aircraft[:5]:
                icao = aircraft.get('hex', 'N/A').upper()
                callsign = self.helpers.format_callsign(aircraft.get('flight', 'N/A'))
                altitude = self.helpers.format_altitude(aircraft.get('alt_baro', 'N/A'))
                online_text += f"**{icao}** ({callsign}) @ {altitude}\n"
            
            if len(matched_aircraft) > 5:
                online_text += f"... and {len(matched_aircraft) - 5} more"
            
            embed.add_field(
                name=_("🟢 Aircraft Online"),
                value=online_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def watchlist_clear(self, ctx):
        """Clear the user's entire watchlist."""
        user_config = self.cog.config.user(ctx.author)
        watchlist = await self.helpers.get_all_watchlist_items(user_config)
        
        total_items = sum(len(items) for items in watchlist.values() if isinstance(items, list))
        if total_items == 0:
            embed = discord.Embed(
                title=_("Watchlist Already Empty"),
                description=_("Your watchlist is already empty."),
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Clear all watchlist data
        empty_watchlist = {'icao': [], 'type': [], 'callsign': [], 'reg': [], 'squawk': []}
        await user_config.watchlist.set(empty_watchlist)
        await user_config.watchlist_notifications.set({})
        await user_config.watchlist_aircraft_state.set({})
        
        embed = discord.Embed(
            title=_("✅ Watchlist Cleared"),
            description=_("Removed **{count}** items from your watchlist.").format(count=total_items),
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    async def watchlist_cooldown(self, ctx, duration: str = None):
        """Set or view the watchlist notification cooldown.
        
        Accepts time formats:
        - Minutes: "20", "20m", "20.5m"
        - Seconds: "30s", "120s"
        - Hours: "1h", "2.5h"
        """
        user_config = self.cog.config.user(ctx.author)
        
        if duration is None:
            # Show current cooldown
            current_cooldown = await user_config.watchlist_cooldown()
            if current_cooldown < 1:
                cooldown_text = _("{seconds} seconds").format(seconds=int(current_cooldown * 60))
            elif current_cooldown == int(current_cooldown):
                cooldown_text = _("{minutes} minutes").format(minutes=int(current_cooldown))
            else:
                cooldown_text = _("{minutes} minutes").format(minutes=current_cooldown)
            
            embed = discord.Embed(
                title=_("Watchlist Cooldown"),
                description=_("Current notification cooldown: **{cooldown}**\n\nUse `{prefix}aircraft watchlist cooldown <duration>` to change it.\n\nExamples: `20m`, `30s`, `1h`, `15.5m`").format(
                    cooldown=cooldown_text,
                    prefix=ctx.prefix
                ),
                color=0xfffffe
            )
            embed.add_field(
                name=_("How it works"),
                value=_("After you receive a notification for a watched aircraft, you won't receive another notification for the same aircraft until the cooldown period expires."),
                inline=False
            )
            embed.add_field(
                name=_("Time formats"),
                value=_("You can use:\n• Minutes: `20`, `20m`, `20.5m`\n• Seconds: `30s`, `120s`\n• Hours: `1h`, `2.5h`"),
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Parse duration string
        try:
            duration = duration.strip().lower()
            minutes = None
            
            if duration.endswith('s'):
                # Convert seconds to minutes
                seconds = float(duration[:-1])
                minutes = seconds / 60.0
            elif duration.endswith('m'):
                # Minutes
                minutes = float(duration[:-1])
            elif duration.endswith('h'):
                # Convert hours to minutes
                hours = float(duration[:-1])
                minutes = hours * 60.0
            else:
                # Assume minutes if no suffix
                minutes = float(duration)
            
            # Validate cooldown value
            if minutes < 0.0167:  # Less than 1 second
                embed = discord.Embed(
                    title=_("Invalid Cooldown"),
                    description=_("Cooldown must be at least 1 second."),
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
            
            if minutes > 1440:  # 24 hours
                embed = discord.Embed(
                    title=_("Invalid Cooldown"),
                    description=_("Cooldown cannot exceed 1440 minutes (24 hours)."),
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
            
            # Set cooldown (store as float to support decimals)
            await user_config.watchlist_cooldown.set(minutes)
            
            # Format response message
            if minutes < 1:
                cooldown_text = _("{seconds} seconds").format(seconds=int(minutes * 60))
            elif minutes == int(minutes):
                cooldown_text = _("{minutes} minutes").format(minutes=int(minutes))
            else:
                cooldown_text = _("{minutes} minutes").format(minutes=minutes)
            
            embed = discord.Embed(
                title=_("✅ Cooldown Updated"),
                description=_("Watchlist notification cooldown set to **{cooldown}**.").format(cooldown=cooldown_text),
                color=0x00ff00
            )
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title=_("Invalid Duration Format"),
                description=_("Invalid duration format. Use a number (e.g. '20'), minutes ('20m'), seconds ('30s'), or hours ('1h').\n\nExamples:\n• `20m` - 20 minutes\n• `30s` - 30 seconds\n• `1h` - 1 hour\n• `15.5m` - 15.5 minutes"),
                color=0xff4545
            )
            await ctx.send(embed=embed)

    # Geo-fence commands
    async def geofence_add(self, ctx, name: str, lat: float, lon: float, radius_nm: float, alert_on: str = "both", cooldown: int = 5, channel: discord.TextChannel = None, role: discord.Role = None):
        """Add a geo-fence alert. Notify when aircraft enter and/or leave the area."""
        if alert_on.lower() not in ("entry", "exit", "both"):
            embed = discord.Embed(title="❌ Invalid alert_on", description="Use: entry, exit, or both", color=0xff0000)
            await ctx.send(embed=embed)
            return
        if radius_nm <= 0 or radius_nm > 500:
            embed = discord.Embed(title="❌ Invalid radius", description="Radius must be 0-500 nautical miles.", color=0xff0000)
            await ctx.send(embed=embed)
            return
        if cooldown < 1 or cooldown > 1440:
            embed = discord.Embed(title="❌ Invalid cooldown", description="Cooldown must be 1-1440 minutes.", color=0xff0000)
            await ctx.send(embed=embed)
            return
        channel = channel or self.cog.bot.get_channel(await self.cog.config.guild(ctx.guild).alert_channel())
        if not channel:
            embed = discord.Embed(title="❌ No channel", description="Set alert channel or pass a channel.", color=0xff0000)
            await ctx.send(embed=embed)
            return
        fence_id = f"geofence_{name.lower().replace(' ', '_')}_{int(datetime.datetime.utcnow().timestamp())}"
        geofence_alerts = await self.cog.config.guild(ctx.guild).geofence_alerts()
        geofence_alerts[fence_id] = {
            "name": name,
            "lat": lat,
            "lon": lon,
            "radius_nm": radius_nm,
            "alert_on": alert_on.lower(),
            "cooldown": cooldown,
            "channel_id": channel.id,
            "role_id": role.id if role else None,
            "aircraft_inside": {},
            "last_alert_time": None,
        }
        await self.cog.config.guild(ctx.guild).geofence_alerts.set(geofence_alerts)
        embed = discord.Embed(
            title="✅ Geo-fence added",
            description=f"**{name}** at ({lat}, {lon}), radius {radius_nm} nm\nAlerts: {alert_on} | Cooldown: {cooldown}m | Channel: {channel.mention}",
            color=0x00ff00,
        )
        embed.add_field(name="ID", value=f"`{fence_id}`", inline=False)
        await ctx.send(embed=embed)

    async def geofence_remove(self, ctx, fence_id: str):
        """Remove a geo-fence alert by ID."""
        geofence_alerts = await self.cog.config.guild(ctx.guild).geofence_alerts()
        if fence_id not in geofence_alerts:
            await ctx.send(f"❌ Geo-fence `{fence_id}` not found.")
            return
        name = geofence_alerts[fence_id].get("name", fence_id)
        del geofence_alerts[fence_id]
        await self.cog.config.guild(ctx.guild).geofence_alerts.set(geofence_alerts)
        await ctx.send(f"✅ Removed geo-fence **{name}** (`{fence_id}`).")

    async def geofence_list(self, ctx):
        """List all geo-fence alerts for this server."""
        geofence_alerts = await self.cog.config.guild(ctx.guild).geofence_alerts()
        if not geofence_alerts:
            embed = discord.Embed(title="Geo-fence alerts", description="No geo-fences configured.", color=0x00aaff)
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title="Geo-fence alerts", description=f"**{len(geofence_alerts)}** geo-fence(s)", color=0x00aaff)
        for fence_id, fence in geofence_alerts.items():
            ch = self.cog.bot.get_channel(fence.get("channel_id"))
            ch_mention = ch.mention if ch else str(fence.get("channel_id"))
            role_id = fence.get("role_id")
            role_mention = f"<@&{role_id}>" if role_id else "—"
            embed.add_field(
                name=fence.get("name", fence_id),
                value=f"**ID:** `{fence_id}`\n**Coords:** ({fence.get('lat')}, {fence.get('lon')}) {fence.get('radius_nm')} nm\n**Alert on:** {fence.get('alert_on', 'both')} | **Cooldown:** {fence.get('cooldown', 5)}m\n**Channel:** {ch_mention} | **Role:** {role_mention}",
                inline=False,
            )
        await ctx.send(embed=embed)
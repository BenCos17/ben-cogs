"""
Aircraft commands for SkySearch cog
"""

import discord
import asyncio
import urllib
import os
from discord.ext import commands
from discord.ext import tasks
from urllib.parse import quote_plus
from redbot.core import commands as red_commands

from ..utils.api import APIManager
from ..utils.helpers import HelperUtils
from ..utils.export import ExportManager


class AircraftCommands:
    """Aircraft-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
        self.api = APIManager(cog)
        self.helpers = HelperUtils(cog)
        self.export = ExportManager(cog)
    
    async def send_aircraft_info(self, ctx, response):
        """Send aircraft information as an embed."""
        # Support both 'aircraft' and 'ac' keys
        aircraft_list = response.get('aircraft') or response.get('ac')
        if aircraft_list:
            await ctx.typing()
            aircraft_data = aircraft_list[0]
            # Get photo for the aircraft
            icao = aircraft_data.get('hex', None)
            if icao:
                icao = icao.upper()
            image_url, photographer = await self.helpers.get_photo_by_hex(icao)
            # Create embed
            embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
            # Create view with buttons
            view = discord.ui.View()
            link = f"https://globe.airplanes.live/?icao={icao}"
            view.add_item(discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=f"{link}", style=discord.ButtonStyle.link))

            # Social media sharing logic 
            import urllib.parse
            ground_speed_knots = aircraft_data.get('gs', 'N/A')
            ground_speed_mph = 'unknown'
            if ground_speed_knots != 'N/A' and ground_speed_knots is not None:
                try:
                    ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
                except Exception:
                    ground_speed_mph = 'unknown'
            squawk_code = aircraft_data.get('squawk', 'N/A')
            emergency_squawk_codes = ['7500', '7600', '7700']
            lat = aircraft_data.get('lat', 'N/A')
            lon = aircraft_data.get('lon', 'N/A')
            if lat != 'N/A' and lat is not None:
                try:
                    lat = round(float(lat), 2)
                    lat_dir = "N" if lat >= 0 else "S"
                    lat = f"{abs(lat)}{lat_dir}"
                except Exception:
                    pass
            if lon != 'N/A' and lon is not None:
                try:
                    lon = round(float(lon), 2)
                    lon_dir = "E" if lon >= 0 else "W"
                    lon = f"{abs(lon)}{lon_dir}"
                except Exception:
                    pass
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
            await ctx.send(embed=embed)

    async def aircraft_by_icao(self, ctx, hex_id: str):
        """Get aircraft information by ICAO hex code."""
        url = f"/?find_hex={hex_id}"
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
            embed = discord.Embed(title="No results found for your query", color=discord.Colour(0xff4545))
            embed.add_field(name="Details", value="No aircraft information found or the response format is incorrect.", inline=False)
            await ctx.send(embed=embed)

    async def aircraft_by_callsign(self, ctx, callsign: str):
        """Get aircraft information by callsign."""
        url = f"/?find_callsign={callsign}"
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="No aircraft found with the specified callsign.", color=0xff4545)
            await ctx.send(embed=embed)

    async def aircraft_by_reg(self, ctx, registration: str):
        """Get aircraft information by registration."""
        url = f"/?find_reg={registration}"
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    async def aircraft_by_type(self, ctx, aircraft_type: str):
        """Get aircraft information by type."""
        url = f"/?find_type={aircraft_type}"
        response = await self.api.make_request(url, ctx)
        if response:
            await self.send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    async def aircraft_by_squawk(self, ctx, squawk_value: str):
        """Get aircraft information by squawk code."""
        url = f"/?all_with_pos&filter_squawk={squawk_value}"
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
            embed = discord.Embed(title="Error", description="Invalid search type specified. Use one of: icao, callsign, squawk, or type.", color=0xfa4545)
            await ctx.send(embed=embed)
            return

        if file_format not in ["csv", "pdf", "txt", "html"]:
            embed = discord.Embed(title="Error", description="Invalid file format specified. Use one of: csv, pdf, txt, or html.", color=0xfa4545)
            await ctx.send(embed=embed)
            return

        # Handle multiple ICAO codes for ICAO search type
        all_aircraft = []
        if search_type == "icao":
            # Split by spaces and clean up each ICAO code
            icao_codes = [code.strip() for code in search_value.split() if code.strip()]
            
            if not icao_codes:
                embed = discord.Embed(title="Error", description="No valid ICAO codes provided.", color=0xfa4545)
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
                embed = discord.Embed(title="Error", description="Invalid search type specified.", color=0xfa4545)
                await ctx.send(embed=embed)
                return

            response = await self.api.make_request(url, ctx)
            if response and response.get('aircraft'):
                all_aircraft = response['aircraft']

        if not all_aircraft:
            embed = discord.Embed(title="Error", description="No aircraft data found.", color=0xfa4545)
            await ctx.send(embed=embed)
            return

        # Export the data
        file_path, aircraft_count = await self.export.export_aircraft_data(
            all_aircraft, search_type, search_value, file_format, ctx
        )
        
        if file_path:
            with open(file_path, 'rb') as fp:
                # Create success embed showing export details
                embed = discord.Embed(title="Export Complete", description=f"Successfully exported {aircraft_count} aircraft to {file_format.upper()} format.", color=0x2BBD8E)
                embed.add_field(name="Search Type", value=search_type.capitalize(), inline=True)
                embed.add_field(name="Search Value", value=search_value, inline=True)
                embed.add_field(name="File Format", value=file_format.upper(), inline=True)
                embed.add_field(name="Aircraft Count", value=f"{aircraft_count} aircraft", inline=True)
                embed.add_field(name="File Name", value=os.path.basename(file_path), inline=True)
                
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

                    photo_url, photographer = await self.helpers.get_photo_by_hex(aircraft_hex)
                    if photo_url:
                        embed.set_image(url=photo_url)
                        if photographer:
                            embed.set_footer(text=f"Photo by {photographer}")
                    return embed

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
        url = f"{self.api.api_url}/?circle={lat},{lon},{radius}"
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
        url = f"{self.api.api_url}/?closest={lat},{lon},{radius}"
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
            image_url, photographer = await self.helpers.get_photo_by_hex(icao)
            if image_url and photographer:
                embed.set_thumbnail(url=image_url)
                embed.set_footer(text=f"Photo by {photographer}")
            else:
                # Set default aircraft image when no photo is available
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                embed.set_footer(text="No photo available")
            
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
        try:
            response = await self.api.make_request(url, ctx)
            if not response:
                embed = discord.Embed(title="Error", description="No response from the API.", color=0xff4545)
                await ctx.send(embed=embed)
                return
            aircraft_list = response.get('aircraft') or response.get('ac')
            if not aircraft_list:
                embed = discord.Embed(title="No results found for your query", color=discord.Colour(0xff4545))
                embed.add_field(name="Details", value="No aircraft information found or the response format is incorrect.", inline=False)
                await ctx.send(embed=embed)
                return
            # Button-based pagination
            import discord
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
                    icao = aircraft_data.get('hex', None)
                    if icao:
                        icao = icao.upper()
                    image_url, photographer = await self.helpers.get_photo_by_hex(icao)
                    embed = self.helpers.create_aircraft_embed(aircraft_data, image_url, photographer)
                    view = discord.ui.View()
                    link = f"https://globe.airplanes.live/?icao={icao}"
                    view.add_item(discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=f"{link}", style=discord.ButtonStyle.link))
                    import urllib.parse
                    ground_speed_knots = aircraft_data.get('gs', 'N/A')
                    ground_speed_mph = 'unknown'
                    if ground_speed_knots != 'N/A' and ground_speed_knots is not None:
                        try:
                            ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
                        except Exception:
                            ground_speed_mph = 'unknown'
                    squawk_code = aircraft_data.get('squawk', 'N/A')
                    emergency_squawk_codes = ['7500', '7600', '7700']
                    lat = aircraft_data.get('lat', 'N/A')
                    lon = aircraft_data.get('lon', 'N/A')
                    if lat != 'N/A' and lat is not None:
                        try:
                            lat = round(float(lat), 2)
                            lat_dir = "N" if lat >= 0 else "S"
                            lat = f"{abs(lat)}{lat_dir}"
                        except Exception:
                            pass
                    if lon != 'N/A' and lon is not None:
                        try:
                            lon = round(float(lon), 2)
                            lon_dir = "E" if lon >= 0 else "W"
                            lon = f"{abs(lon)}{lon_dir}"
                        except Exception:
                            pass
                    if squawk_code in emergency_squawk_codes:
                        tweet_text = f"Spotted an aircraft declaring an emergency! #Squawk #{squawk_code}, flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. #SkySearch #Emergency\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
                    else:
                        tweet_text = f"Tracking flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph using #SkySearch\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
                    tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote_plus(tweet_text)}"
                    view.add_item(discord.ui.Button(label=f"Post on 𝕏", emoji="📣", url=tweet_url, style=discord.ButtonStyle.link))
                    whatsapp_text = f"Check out this aircraft! Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. Track live @ https://globe.airplanes.live/?icao={icao} #SkySearch"
                    whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote_plus(whatsapp_text)}"
                    view.add_item(discord.ui.Button(label="Send on WhatsApp", emoji="📱", url=whatsapp_url, style=discord.ButtonStyle.link))
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
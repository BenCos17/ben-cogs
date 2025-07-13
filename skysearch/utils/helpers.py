"""
Helper utilities for SkySearch cog
"""

import aiohttp
import discord
from urllib.parse import quote_plus


class HelperUtils:
    """Helper utilities for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
    
    async def get_photo_by_hex(self, hex_id, registration=None):
        """Get aircraft photo by hex ICAO or registration."""
        if not hasattr(self.cog, '_http_client'):
            self.cog._http_client = aiohttp.ClientSession()
        
        # Fetch photo by hex ICAO
        try:
            async with self.cog._http_client.get(f'https://api.planespotters.net/pub/photos/reg/{hex_id}') as response:
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
                async with self.cog._http_client.get(f'https://api.planespotters.net/pub/photos/reg/{registration}') as response:
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
    
    def create_aircraft_embed(self, aircraft_data, image_url=None, photographer=None):
        """Create a Discord embed for aircraft information."""
        emergency_squawk_codes = ['7500', '7600', '7700']
        hex_id = aircraft_data.get('hex', '')
        registration = aircraft_data.get('reg', '')
        link = f"https://globe.airplanes.live/?icao={hex_id}"
        squawk_code = aircraft_data.get('squawk', 'N/A')
        description = f"{aircraft_data.get('desc', 'N/A')}"
        
        if aircraft_data.get('year', None) is not None:
            description += f" ({aircraft_data.get('year')})"
        
        # Set embed color based on squawk code
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
        
        # Add basic aircraft information
        callsign = aircraft_data.get('flight', 'N/A').strip()
        if not callsign or callsign == 'N/A':
            callsign = 'BLOCKED'
        embed.add_field(name="Callsign", value=f"{callsign}", inline=True)
        
        if registration is not None:
            registration = registration.upper()
            embed.add_field(name="Registration", value=f"{registration}", inline=True)
        
        icao = aircraft_data.get('hex', 'N/A').upper()
        embed.add_field(name="ICAO", value=f"{icao}", inline=True)
        
        # Add altitude information
        altitude = aircraft_data.get('alt_baro', 'N/A')
        if altitude == 'ground':
            embed.add_field(name="Status", value="On ground", inline=True)
        elif altitude != 'N/A':
            if isinstance(altitude, int):
                altitude = "{:,}".format(altitude)
            altitude_feet = f"{altitude} ft"
            embed.add_field(name="Altitude", value=f"{altitude_feet}", inline=True)
        
        # Add heading information
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
        
        # Add position information
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
        
        # Add aircraft model
        aircraft_model = aircraft_data.get('t', None)
        if aircraft_model is not None:
            embed.add_field(name="Model", value=f"{aircraft_model}", inline=True)
        
        # Add speed information
        ground_speed_knots = aircraft_data.get('gs', 'N/A')
        if ground_speed_knots != 'N/A':
            ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
            embed.add_field(name="Speed", value=f"{ground_speed_mph} mph", inline=True)
        
        # Add category information
        category_code_to_label = {
            "A0": "No info available", "A1": "Light aircraft", "A2": "Small aircraft",
            "A3": "Large aircraft", "A4": "High vortex large aircraft", "A5": "Heavy aircraft",
            "A6": "High performance aircraft", "A7": "Rotorcraft", "B0": "No info available",
            "B1": "Glider / sailplane", "B2": "Lighter-than-air", "B3": "Parachutist / skydiver",
            "B4": "Ultralight / hang-glider / paraglider", "B5": "Reserved", "B6": "UAV",
            "B7": "Space / trans-atmospheric vehicle", "C0": "No info available",
            "C1": "Emergency vehicle", "C2": "Service vehicle", "C3": "Point obstacle",
            "C4": "Cluster obstacle", "C5": "Line obstacle", "C6": "Reserved", "C7": "Reserved"
        }
        category = aircraft_data.get('category', None)
        if category is not None:
            category_label = category_code_to_label.get(category, "Unknown category")
            embed.add_field(name="Category", value=f"{category_label}", inline=True)

        # Add operator information
        operator = aircraft_data.get('ownOp', None)
        if operator is not None:
            operator_encoded = quote_plus(operator)
            embed.add_field(name="Operated by", value=f"[{operator}](https://www.google.com/search?q={operator_encoded})", inline=True)
        
        # Add timing information
        last_seen = aircraft_data.get('seen', 'N/A')
        if last_seen != 'N/A':
            last_seen_text = "Just now" if float(last_seen) < 1 else f"{int(float(last_seen))} seconds ago"
            embed.add_field(name="Last signal", value=last_seen_text, inline=True)
        
        last_seen_pos = aircraft_data.get('seen_pos', 'N/A')
        if last_seen_pos != 'N/A':
            last_seen_pos_text = "Just now" if float(last_seen_pos) < 1 else f"{int(float(last_seen_pos))} seconds ago"
            embed.add_field(name="Last position", value=last_seen_pos_text, inline=True)
        
        # Add altitude trend information
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

        # Add asset intelligence information
        icao = aircraft_data.get('hex', None).upper()
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
        if image_url and photographer:
            embed.set_thumbnail(url=image_url)
            embed.set_footer(text=f"Photo by {photographer}")
        else:
            # Set default aircraft image when no photo is available
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            embed.set_footer(text="No photo available")

        return embed 
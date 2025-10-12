"""
Helper utilities for SkySearch cog
"""

import json
import aiohttp
import discord
from urllib.parse import quote_plus


class HelperUtils:
    """Helper utilities for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
    
    def _ensure_http_client(self):
        """Ensure HTTP client is initialized."""
        if not hasattr(self.cog, '_http_client'):
            self.cog._http_client = aiohttp.ClientSession()
    
    async def get_photo_by_hex(self, hex_id, registration=None):
        """
        Get aircraft photo by hex ICAO or registration.
        
        Args:
            hex_id (str): Aircraft hex ICAO code
            registration (str, optional): Aircraft registration code
            
        Returns:
            tuple: (image_url, photographer) or (None, None) if no photo found
        """
        self._ensure_http_client()
        
        # First try to get photo by hex ICAO directly
        if hex_id:
            try:
                async with self.cog._http_client.get(f'https://api.planespotters.net/pub/photos/hex/{hex_id}') as response:
                    if response.status == 200:
                        json_out = await response.json()
                        if 'photos' in json_out and json_out['photos']:
                            photo = json_out['photos'][0]
                            url = photo.get('thumbnail_large', {}).get('src', '')
                            photographer = photo.get('photographer', '')
                            if url:  # Only return if we got a valid URL
                                return url, photographer
            except (KeyError, IndexError, aiohttp.ClientError):
                pass

        # If no photo found by hex, try by registration if provided
        if registration:
            try:
                async with self.cog._http_client.get(f'https://api.planespotters.net/pub/photos/reg/{registration}') as response:
                    if response.status == 200:
                        json_out = await response.json()
                        if 'photos' in json_out and json_out['photos']:
                            photo = json_out['photos'][0]
                            url = photo.get('thumbnail_large', {}).get('src', '')
                            photographer = photo.get('photographer', '')
                            if url:  # Only return if we got a valid URL
                                return url, photographer
            except (KeyError, IndexError, aiohttp.ClientError):
                pass

        # If still no photo found, try to get aircraft data to find registration and try again
        if hex_id:
            try:
                # Get aircraft data from airplanes.live to find registration
                api_url = await self.cog.api.get_api_url()
                url = f"{api_url}/?find_hex={hex_id}"
                response = await self.cog.api.make_request(url)
                
                if response and 'aircraft' in response and response['aircraft']:
                    aircraft_data = response['aircraft'][0]
                    reg = aircraft_data.get('reg')
                    
                    if reg and reg != registration:  # Only try if we haven't already tried this registration
                        # try to get photo using the registration
                        try:
                            async with self.cog._http_client.get(f'https://api.planespotters.net/pub/photos/reg/{reg}') as response:
                                if response.status == 200:
                                    json_out = await response.json()
                                    if 'photos' in json_out and json_out['photos']:
                                        photo = json_out['photos'][0]
                                        url = photo.get('thumbnail_large', {}).get('src', '')
                                        photographer = photo.get('photographer', '')
                                        if url:  # Only return if we got a valid URL
                                            return url, photographer
                        except (KeyError, IndexError, aiohttp.ClientError):
                            pass
            except Exception:
                pass

        return None, None  # Return None if no photo found

    async def get_photo_by_aircraft_data(self, aircraft_data):
        """
        Get aircraft photo using full aircraft data (preferred method).
        
        Args:
            aircraft_data (dict): Complete aircraft data dictionary
            
        Returns:
            tuple: (image_url, photographer) or (None, None) if no photo found
        """
        hex_id = aircraft_data.get('hex', '')
        registration = aircraft_data.get('reg', '')
        
        # Clean up the data
        if hex_id:
            hex_id = hex_id.upper()
        if registration and registration != 'N/A':
            registration = registration.upper()
        else:
            registration = None
            
        return await self.get_photo_by_hex(hex_id, registration)
    
    def create_aircraft_embed(self, aircraft_data, image_url=None, photographer=None):
        """
        Create a Discord embed for aircraft information.
        
        Args:
            aircraft_data (dict): Aircraft data dictionary
            image_url (str, optional): URL of aircraft image
            photographer (str, optional): Name of photographer
            
        Returns:
            discord.Embed: Formatted Discord embed
        """
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
            try:
                # Try to use local icon first
                icon_path = self.cog.get_airplane_icon_path()
                if icon_path.exists():
                    embed.set_thumbnail(url=f"attachment://defaultairplane.png")
                else:
                    # Fallback to external URL
                    embed.set_thumbnail(url="https://raw.githubusercontent.com/BenCos17/ben-cogs/main/skysearch/data/defaultairplane.png")
            except Exception:
                # Fallback to external URL
                embed.set_thumbnail(url="https://raw.githubusercontent.com/BenCos17/ben-cogs/main/skysearch/data/defaultairplane.png")
            embed.set_footer(text="No photo available")

        return embed

    async def get_airport_data(self, airport_code: str):
        """Get airport information by ICAO or IATA code."""
        self._ensure_http_client()
        
        try:
            # Try airport-data.com API
            url = f"https://airport-data.com/api/ap_info.json?icao={airport_code}"
            async with self.cog._http_client.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and not isinstance(data, list):  # Valid airport data
                        return {
                            'name': data.get('name', 'N/A'),
                            'city': data.get('city', 'N/A'),
                            'country': data.get('country', 'N/A'),
                            'latitude': data.get('latitude', 'N/A'),
                            'longitude': data.get('longitude', 'N/A'),
                            'elevation': data.get('elevation', 'N/A'),
                            'timezone': data.get('timezone', 'N/A')
                        }
        except (aiohttp.ClientError, KeyError, ValueError):
            pass

        return None
        


    async def get_airport_image(self, lat: str, lon: str):
        """Get airport satellite image using OpenStreetMap static maps."""
        if lat == 'N/A' or lon == 'N/A':
            return None
        
        try:
            # Use OpenStreetMap static maps (free, no API key required)
            # This provides satellite imagery via OpenStreetMap's tile servers
            url = f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lon}&zoom=14&size=600x400&maptype=mapnik&markers={lat},{lon},red"
            return url
        except Exception:
            return None

    async def get_runway_data(self, airport_code: str):
        """Get runway information for an airport."""
        self._ensure_http_client()
        
        try:
            # Try airportdb.io API
            url = f"https://airportdb.io/api/v1/airports/{airport_code}"
            async with self.cog._http_client.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and 'runways' in data:
                        return {
                            'runways': data['runways']
                        }
        except (aiohttp.ClientError, KeyError, ValueError):
            pass
        
        return None

    async def get_navaid_data(self, airport_code: str):
        """Get navigational aids for an airport."""
        self._ensure_http_client()
        
        try:
            # Try airportdb.io API for navaids
            url = f"https://airportdb.io/api/v1/airports/{airport_code}/navaids"
            async with self.cog._http_client.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and 'navaids' in data:
                        return {
                            'navaids': data['navaids']
                        }
        except (aiohttp.ClientError, KeyError, ValueError):
            pass
        
        return None


    # for feeder link command stuff
    async def parse_json_input(self, json_input: str):
        """
        Parse JSON input from either a URL or direct JSON text.
        
        Args:
            json_input (str): Either a URL containing JSON data OR direct JSON text
            
        Returns:
            dict: Parsed JSON data
            
        Raises:
            ValueError: If JSON is invalid or URL fails
            aiohttp.ClientError: If URL request fails
        """
        # Check if input looks like a URL
        if json_input.startswith(('http://', 'https://')):
            # Fetch the JSON data from the URL
            self._ensure_http_client()
            
            async with self.cog._http_client.get(json_input) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch JSON data. Status: {response.status}")
                
                return await response.json()
        else:
            # Try to parse as direct JSON
            try:
                return json.loads(json_input)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")

    def create_feeder_embed(self, json_data: dict):
        """
        Create a Discord embed for feeder information.
        
        Args:
            json_data (dict): Parsed feeder JSON data
            
        Returns:
            discord.Embed: Formatted Discord embed
        """
        embed = discord.Embed(
            title="Feeder Information", 
            color=0x00ff00
        )
        
        # Extract host information
        host = json_data.get('host', 'Unknown')
        embed.add_field(name="Host", value=host, inline=True)
        
        # Extract map link if available
        map_link = json_data.get('map_link')
        if map_link:
            embed.add_field(name="Map Link", value=f"[View on Globe]({map_link})", inline=False)
            embed.url = map_link
        
        # Extract beast clients information
        beast_clients = json_data.get('beast_clients', [])
        if beast_clients:
            embed.add_field(name="Beast Clients", value=f"{len(beast_clients)} active", inline=True)
            
            # Show details for first few clients
            client_details = []
            for i, client in enumerate(beast_clients[:3]):  # Show max 3 clients
                uuid = client.get('uuid', 'Unknown')[:8] + '...'  # Truncate UUID
                msgs_s = client.get('msgs_s', 0)
                pos_s = client.get('pos_s', 0)
                client_details.append(f"`{uuid}`: {msgs_s:.1f} msg/s, {pos_s:.1f} pos/s")
            
            if client_details:
                embed.add_field(name="Client Details", value='\n'.join(client_details), inline=False)
        
        # Extract mlat clients information
        mlat_clients = json_data.get('mlat_clients', [])
        if mlat_clients:
            embed.add_field(name="MLAT Clients", value=f"{len(mlat_clients)} active", inline=True)
            
            # Show details for first few mlat clients
            mlat_details = []
            for i, client in enumerate(mlat_clients[:2]):  # Show max 2 mlat clients
                user = client.get('user', 'Unknown')
                message_rate = client.get('message_rate', 0)
                peer_count = client.get('peer_count', 0)
                mlat_details.append(f"`{user}`: {message_rate} msg/s, {peer_count} peers")
            
            if mlat_details:
                embed.add_field(name="MLAT Details", value='\n'.join(mlat_details), inline=False)
        
        # Add timestamp
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Feeder data extracted from JSON")
        
        return embed

    def create_feeder_view(self, json_input: str, json_data: dict = None):
        """
        Create a Discord view with buttons for feeder information.
        
        Args:
            json_input (str): Original JSON input (for URL detection)
            json_data (dict, optional): Parsed JSON data for additional buttons
            
        Returns:
            discord.ui.View: View with interactive buttons
        """
        view = discord.ui.View()
        
        # Add main map link button
        map_link = json_data.get('map_link') if json_data else None
        if map_link:
            view.add_item(discord.ui.Button(
                label="View on Globe", 
                emoji="🌍", 
                url=map_link, 
                style=discord.ButtonStyle.link
            ))
        
        # Add individual Beast client feed buttons
        if json_data:
            beast_clients = json_data.get('beast_clients', [])
            for i, client in enumerate(beast_clients[:5]):  # Limit to 5 buttons
                uuid = client.get('uuid', '')
                if uuid:
                    # Create individual feed URL - use first 16 characters of UUID without hyphens
                    # This matches the pattern from the map_link in the JSON
                    feed_uuid = uuid.replace('-', '')[:16]
                    feed_url = f"https://globe.airplanes.live/?feed={feed_uuid}"
                    view.add_item(discord.ui.Button(
                        label=f"Feed {i+1}", 
                        emoji="📡", 
                        url=feed_url, 
                        style=discord.ButtonStyle.link
                    ))
        
        # Add button to view raw JSON (only if it's a URL)
        if json_input.startswith(('http://', 'https://')):
            view.add_item(discord.ui.Button(
                label="View Raw JSON", 
                emoji="📄", 
                url=json_input, 
                style=discord.ButtonStyle.link
            ))
        
        return view 
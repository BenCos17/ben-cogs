"""
Helper utilities for SkySearch cog
"""

import json
import aiohttp
import discord
from urllib.parse import quote_plus, urlparse, parse_qs, urlencode
import asyncio


class HelperUtils:
    """Helper utilities for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
    
    def _ensure_http_client(self):
        """Ensure HTTP client is initialized."""
        if not hasattr(self.cog, '_http_client'):
            self.cog._http_client = aiohttp.ClientSession()

    async def _get_http_headers(self) -> dict:
        """Get outbound HTTP headers (includes configured User-Agent if set)."""
        headers = {}
        try:
            user_agent = await self.cog.config.user_agent()
            if user_agent:
                headers["User-Agent"] = user_agent
        except Exception:
            # In case config isn't available for some reason, fall back to aiohttp defaults.
            pass
        return headers
    
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
                async with self.cog._http_client.get(
                    f'https://api.planespotters.net/pub/photos/hex/{hex_id}',
                    headers=await self._get_http_headers(),
                ) as response:
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
                async with self.cog._http_client.get(
                    f'https://api.planespotters.net/pub/photos/reg/{registration}',
                    headers=await self._get_http_headers(),
                ) as response:
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
                            async with self.cog._http_client.get(
                                f'https://api.planespotters.net/pub/photos/reg/{reg}',
                                headers=await self._get_http_headers(),
                            ) as response:
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
            async with self.cog._http_client.get(url, headers=await self._get_http_headers()) as response:
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
            # Try airportdb.io API (support both /airport/ and legacy /airports/ paths)
            token = await self._get_airportdb_token()
            base_paths = [
                f"https://airportdb.io/api/v1/airport/{airport_code}",
                f"https://airportdb.io/api/v1/airports/{airport_code}",
            ]

            for base in base_paths:
                url = base
                if token:
                    url = f"{base}?{urlencode({'apiToken': token})}"

                try:
                    async with self.cog._http_client.get(url, headers=await self._get_http_headers()) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and 'runways' in data:
                                return {'runways': data['runways']}
                except (aiohttp.ClientError, KeyError, ValueError):
                    # Try next path variant
                    continue
        except Exception:
            pass

        return None

    async def get_navaid_data(self, airport_code: str):
        """Get navigational aids for an airport."""
        self._ensure_http_client()
        try:
            # Prefer documented single-airport endpoint which accepts `apiToken` as query param
            token = await self._get_airportdb_token()
            base_paths = [
                f"https://airportdb.io/api/v1/airport/{airport_code}",
                f"https://airportdb.io/api/v1/airport/{airport_code}/navaids",
                f"https://airportdb.io/api/v1/airports/{airport_code}/navaids",
            ]

            for base in base_paths:
                url = base
                if token:
                    url = f"{base}?{urlencode({'apiToken': token})}"

                try:
                    async with self.cog._http_client.get(url, headers=await self._get_http_headers()) as response:
                        if response.status == 200:
                            data = await response.json()
                            # If the airport object contains navaids
                            if data and isinstance(data, dict) and 'navaids' in data:
                                return {'navaids': data['navaids']}
                            # Some endpoints may return a wrapper with 'navaids' key at top-level
                            if data and isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict) and 'navaids' in data['data']:
                                return {'navaids': data['data']['navaids']}
                except (aiohttp.ClientError, KeyError, ValueError):
                    # Try next path variant
                    continue
        except Exception:
            pass

        return None

    async def _get_airportdb_token(self) -> str | None:
        """Retrieve Airportdb API token from Red's shared API tokens.

        Looks for the `airportdbio` shared token and returns the `api_token` value
        (supports async or sync `get_shared_api_tokens` implementations).
        """
        try:
            getter = getattr(self.cog.bot, 'get_shared_api_tokens', None)
            if not getter:
                return None

            tokens = getter('airportdbio')
            if asyncio.iscoroutine(tokens):
                tokens = await tokens

            if not tokens:
                return None

            # Common key from install instructions is `api_token`
            return tokens.get('api_token') or tokens.get('apiToken') or tokens.get('token')
        except Exception:
            return None


    # for feeder link command stuff
    def _globe_feed_url(self, ids: list, param: str = "uuid") -> str:
        """
        Build a globe.airplanes.live URL for one or more feed UUIDs.
        Supports both ?uuid= and ?feed= so either param works for feed info.
        """
        if not ids:
            return "https://globe.airplanes.live/"
        # IDs are 16-char hex (no hyphens)
        value = ",".join(ids) if len(ids) > 1 else ids[0]
        return f"https://globe.airplanes.live/?{param}={value}"

    def _normalize_globe_feed_link(self, url: str) -> str:
        """
        Normalize a globe.airplanes.live URL so both ?uuid and ?feed work.
        If the URL has ?feed= or ?uuid=, keep it as-is (both work on the site).
        """
        if not url or "globe.airplanes.live" not in url:
            return url
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        # Prefer uuid for multi-feed, otherwise keep existing param
        feed_val = qs.get("feed", qs.get("uuid"))
        if feed_val:
            # Keep first param we found so link format is preserved
            return url
        return url

    def get_feed_map_link(self, json_data: dict) -> str | None:
        """
        Get map link for feeder info. Uses map_link from JSON if present
        (supports both ?uuid= and ?feed=). Otherwise builds from beast_clients.
        """
        map_link = json_data.get("map_link") if json_data else None
        if map_link:
            return self._normalize_globe_feed_link(map_link)
        beast_clients = json_data.get("beast_clients", []) if json_data else []
        ids = []
        for client in beast_clients:
            uuid_val = client.get("uuid") or ""
            if uuid_val:
                feed_id = uuid_val.replace("-", "")[:16]
                if feed_id and feed_id not in ids:
                    ids.append(feed_id)
        if ids:
            return self._globe_feed_url(ids, param="uuid")
        return None

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
            
            async with self.cog._http_client.get(json_input, headers=await self._get_http_headers()) as response:
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
        
        # Extract map link if available (?uuid and ?feed both supported)
        map_link = self.get_feed_map_link(json_data)
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
        
        # Add main map link button (?uuid and ?feed both supported)
        map_link = self.get_feed_map_link(json_data) if json_data else None
        if map_link:
            view.add_item(discord.ui.Button(
                label="View on Globe", 
                emoji="🌍", 
                url=map_link, 
                style=discord.ButtonStyle.link
            ))
        
        # Add individual Beast client feed buttons (use ?feed= for single; ?uuid= also works)
        if json_data:
            beast_clients = json_data.get('beast_clients', [])
            for i, client in enumerate(beast_clients[:5]):  # Limit to 5 buttons
                uuid = client.get('uuid', '')
                if uuid:
                    # Create individual feed URL - both ?feed= and ?uuid= work on globe
                    feed_uuid = uuid.replace('-', '')[:16]
                    feed_url = self._globe_feed_url([feed_uuid], param="feed")
                    
                    # Create feed name using first part of UUID
                    # Use first 8 characters of UUID for a clean, short identifier
                    feed_name = uuid[:8]
                    
                    # Add performance info if available
                    msgs_s = client.get('msgs_s', 0)
                    if msgs_s > 0:
                        feed_name += f" ({msgs_s:.1f} msg/s)"
                    
                    # Truncate if too long for Discord button (max 80 characters)
                    if len(feed_name) > 80:
                        feed_name = feed_name[:77] + "..."
                    
                    view.add_item(discord.ui.Button(
                        label=feed_name, 
                        emoji="📡", 
                        url=feed_url, 
                        style=discord.ButtonStyle.link
                    ))
        
        # Note: MLAT clients don't have individual feed URLs like beast clients
        # They are part of the overall feeder system, so we don't create individual buttons for them
        # The MLAT information is already displayed in the embed above
        
        # Add button to view raw JSON (only if it's a URL)
        if json_input.startswith(('http://', 'https://')):
            view.add_item(discord.ui.Button(
                label="View Raw JSON", 
                emoji="📄", 
                url=json_input, 
                style=discord.ButtonStyle.link
            ))
        
        return view
    
    def format_altitude(self, altitude):
        """
        Format altitude value for display.
        
        Args:
            altitude: Altitude value (can be 'ground', 'N/A', int, or str)
            
        Returns:
            str: Formatted altitude text
        """
        if altitude == 'ground':
            return "On ground"
        elif altitude != 'N/A' and altitude is not None:
            if isinstance(altitude, (int, float)):
                return f"{int(altitude):,} ft"
            return f"{altitude} ft"
        return "N/A"
    
    def format_speed(self, speed_knots):
        """
        Format speed from knots to mph for display.
        
        Args:
            speed_knots: Speed in knots (can be 'N/A', None, int, or float)
            
        Returns:
            str: Formatted speed text in mph
        """
        if speed_knots != 'N/A' and speed_knots is not None:
            try:
                speed_mph = round(float(speed_knots) * 1.15078)
                return f"{speed_mph} mph"
            except (ValueError, TypeError):
                return "N/A"
        return "N/A"
    
    def format_position(self, lat, lon):
        """
        Format latitude and longitude for display.
        
        Args:
            lat: Latitude value
            lon: Longitude value
            
        Returns:
            str: Formatted position text or "N/A"
        """
        if lat != 'N/A' and lat is not None and lon != 'N/A' and lon is not None:
            try:
                lat_rounded = round(float(lat), 2)
                lon_rounded = round(float(lon), 2)
                return f"{lat_rounded}, {lon_rounded}"
            except (ValueError, TypeError):
                return "N/A"
        return "N/A"
    
    def format_callsign(self, callsign):
        """
        Format callsign for display (handles blocked/empty callsigns).
        
        Args:
            callsign: Callsign string
            
        Returns:
            str: Formatted callsign or "BLOCKED"
        """
        if not callsign or callsign.strip() == '' or callsign == 'N/A':
            return 'BLOCKED'
        return callsign.strip()
    
    def validate_icao(self, icao):
        """
        Validate ICAO hex code format.
        
        Args:
            icao: ICAO code to validate
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        icao = icao.upper().strip()
        if len(icao) != 6:
            return False, "ICAO code must be exactly 6 characters."
        if not all(c in '0123456789ABCDEF' for c in icao):
            return False, "ICAO code must contain only hexadecimal characters (0-9, A-F)."
        return True, None
    
    def create_watchlist_notification_embed(self, icao, aircraft_data):
        """
        Create a notification embed for watchlist aircraft coming online.
        
        Args:
            icao: ICAO hex code
            aircraft_data: Aircraft data dictionary
            
        Returns:
            discord.Embed: Formatted notification embed
        """
        from redbot.core.i18n import Translator
        _watchlist = Translator("Skysearch", __file__)
        
        embed = discord.Embed(
            title=_watchlist("🟢 Aircraft Online"),
            description=_watchlist("**{icao}** from your watchlist is now online!").format(icao=icao),
            color=0x00ff00
        )
        
        callsign = self.format_callsign(aircraft_data.get('flight', 'N/A'))
        altitude = self.format_altitude(aircraft_data.get('alt_baro', 'N/A'))
        speed = self.format_speed(aircraft_data.get('gs', 'N/A'))
        position = self.format_position(
            aircraft_data.get('lat', 'N/A'),
            aircraft_data.get('lon', 'N/A')
        )
        
        # Determine status
        is_landed = self.is_aircraft_landed(aircraft_data)
        status = _watchlist("On ground") if is_landed else _watchlist("In flight")
        
        embed.add_field(name=_watchlist("Status"), value=status, inline=True)
        embed.add_field(name=_watchlist("Callsign"), value=callsign, inline=True)
        embed.add_field(name=_watchlist("Altitude"), value=altitude, inline=True)
        embed.add_field(name=_watchlist("Speed"), value=speed, inline=True)
        embed.add_field(name=_watchlist("Position"), value=position, inline=False)
        
        return embed
    
    def create_watchlist_view(self, icao):
        """
        Create a view with buttons for watchlist aircraft.
        
        Args:
            icao: ICAO hex code
            
        Returns:
            discord.ui.View: View with link button
        """
        view = discord.ui.View()
        link = f"https://globe.airplanes.live/?icao={icao}"
        view.add_item(discord.ui.Button(
            label="View on airplanes.live",
            emoji="🗺️",
            url=link,
            style=discord.ButtonStyle.link
        ))
        return view
    
    def extract_aircraft_status(self, aircraft_data):
        """
        Extract formatted status information from aircraft data.
        
        Args:
            aircraft_data: Aircraft data dictionary
            
        Returns:
            dict: Dictionary with formatted status fields (callsign, altitude, speed, position)
        """
        return {
            'callsign': self.format_callsign(aircraft_data.get('flight', 'N/A')),
            'altitude': self.format_altitude(aircraft_data.get('alt_baro', 'N/A')),
            'speed': self.format_speed(aircraft_data.get('gs', 'N/A')),
            'position': self.format_position(
                aircraft_data.get('lat', 'N/A'),
                aircraft_data.get('lon', 'N/A')
            )
        }
    
    def is_aircraft_landed(self, aircraft_data):
        """
        Check if aircraft is landed based on altitude.
        
        Args:
            aircraft_data: Aircraft data dictionary
            
        Returns:
            bool: True if aircraft is landed (altitude < 25 or 'ground'), False otherwise
        """
        altitude = aircraft_data.get('altitude') or aircraft_data.get('alt_baro')
        if altitude == 'ground':
            return True
        if altitude is not None and altitude != 'N/A':
            try:
                return float(altitude) < 25
            except (ValueError, TypeError):
                return False
        return False
    
    def create_watchlist_landing_embed(self, icao, aircraft_data):
        """
        Create a landing notification embed for watchlist aircraft.
        
        Args:
            icao: ICAO hex code
            aircraft_data: Aircraft data dictionary
            
        Returns:
            discord.Embed: Formatted landing notification embed
        """
        from redbot.core.i18n import Translator
        _watchlist = Translator("Skysearch", __file__)
        
        embed = discord.Embed(
            title=_watchlist("🛬 Aircraft Landed"),
            description=_watchlist("**{icao}** from your watchlist has landed!").format(icao=icao),
            color=0x00ff00
        )
        
        callsign = self.format_callsign(aircraft_data.get('flight', 'N/A'))
        position = self.format_position(
            aircraft_data.get('lat', 'N/A'),
            aircraft_data.get('lon', 'N/A')
        )
        
        embed.add_field(name=_watchlist("Status"), value=_watchlist("On ground"), inline=True)
        embed.add_field(name=_watchlist("Callsign"), value=callsign, inline=True)
        embed.add_field(name=_watchlist("Position"), value=position, inline=False)
        
        return embed
    
    def create_watchlist_takeoff_embed(self, icao, aircraft_data):
        """
        Create a takeoff notification embed for watchlist aircraft.
        
        Args:
            icao: ICAO hex code
            aircraft_data: Aircraft data dictionary
            
        Returns:
            discord.Embed: Formatted takeoff notification embed
        """
        from redbot.core.i18n import Translator
        _watchlist = Translator("Skysearch", __file__)
        
        embed = discord.Embed(
            title=_watchlist("✈️ Aircraft Took Off"),
            description=_watchlist("**{icao}** from your watchlist has taken off!").format(icao=icao),
            color=0x0099ff
        )
        
        callsign = self.format_callsign(aircraft_data.get('flight', 'N/A'))
        altitude = self.format_altitude(aircraft_data.get('alt_baro', 'N/A'))
        speed = self.format_speed(aircraft_data.get('gs', 'N/A'))
        position = self.format_position(
            aircraft_data.get('lat', 'N/A'),
            aircraft_data.get('lon', 'N/A')
        )
        
        embed.add_field(name=_watchlist("Status"), value=_watchlist("In flight"), inline=True)
        embed.add_field(name=_watchlist("Callsign"), value=callsign, inline=True)
        embed.add_field(name=_watchlist("Altitude"), value=altitude, inline=True)
        embed.add_field(name=_watchlist("Speed"), value=speed, inline=True)
        embed.add_field(name=_watchlist("Position"), value=position, inline=False)
        
        return embed


class JSONInputModal(discord.ui.Modal):
    """Modal for securely inputting JSON data."""
    
    def __init__(self, cog):
        super().__init__(title="Input Feeder JSON Data")
        self.cog = cog
        
        # Add text input for JSON data
        self.json_input = discord.ui.TextInput(
            label="JSON Data or URL",
            placeholder="Paste your JSON data here or enter a URL containing JSON...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000  # Discord's limit for text inputs
        )
        self.add_item(self.json_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        json_input = self.json_input.value.strip()
        
        if not json_input:
            embed = discord.Embed(
                title="Error", 
                description="JSON input cannot be empty.", 
                color=0xff4545
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Parse JSON input using utility function
            json_data = await self.cog.helpers.parse_json_input(json_input)
            
            # Create embed using utility function
            embed = self.cog.helpers.create_feeder_embed(json_data)
            
            # Create view using utility function
            view = self.cog.helpers.create_feeder_view(json_input, json_data)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except ValueError as e:
            embed = discord.Embed(
                title="Error", 
                description=str(e), 
                color=0xff4545
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="Error", 
                description=f"Failed to parse JSON data: {str(e)}", 
                color=0xff4545
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class JSONInputButton(discord.ui.View):
    """Button view to trigger JSON input modal."""
    
    def __init__(self, cog):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
    
    @discord.ui.button(label="Input JSON Data", style=discord.ButtonStyle.primary, emoji="📄")
    async def input_json_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open modal to input JSON data."""
        modal = JSONInputModal(self.cog)
        await interaction.response.send_modal(modal) 
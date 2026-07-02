"""Google Maps link parser for extracting coordinates."""
import re
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple


class MapParser:
    """Parse Google Maps links to extract latitude and longitude."""

    @staticmethod
    def parse_maps_url(url: str) -> Optional[Tuple[float, float]]:
        """
        Extract coordinates from various Google Maps URL formats.
        
        Supported formats:
        - https://maps.google.com/?q=40.7128,-74.0060
        - https://www.google.com/maps/place/40.7128,-74.0060
        - https://maps.google.com/maps?q=40.7128,-74.0060
        - https://www.google.com/maps/@40.7128,-74.0060,15z
        
        Args:
            url: Google Maps URL
            
        Returns:
            Tuple of (latitude, longitude) or None if parsing fails
        """
        try:
            # Remove whitespace
            url = url.strip()
            
            # Try standard coordinates pattern: lat,lng
            coord_pattern = r'([-+]?\d+\.?\d*)[,\s]+([-+]?\d+\.?\d*)'
            
            # Check for @lat,lng,zoom format (modern Google Maps)
            at_match = re.search(r'@([-+]?\d+\.?\d*),([-+]?\d+\.?\d*)', url)
            if at_match:
                lat, lng = float(at_match.group(1)), float(at_match.group(2))
                return MapParser._validate_coords(lat, lng)
            
            # Check for ?q=lat,lng or &q=lat,lng format
            q_match = re.search(r'[?&]q=([-+]?\d+\.?\d*)[,\s]+([-+]?\d+\.?\d*)', url)
            if q_match:
                lat, lng = float(q_match.group(1)), float(q_match.group(2))
                return MapParser._validate_coords(lat, lng)
            
            # Check for /place/lat,lng format
            place_match = re.search(r'/place/([-+]?\d+\.?\d*)[,\s]+([-+]?\d+\.?\d*)', url)
            if place_match:
                lat, lng = float(place_match.group(1)), float(place_match.group(2))
                return MapParser._validate_coords(lat, lng)
            
            # Parse query string for 'q' parameter
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'q' in query_params:
                q_value = query_params['q'][0]
                coord_match = re.search(coord_pattern, q_value)
                if coord_match:
                    lat, lng = float(coord_match.group(1)), float(coord_match.group(2))
                    return MapParser._validate_coords(lat, lng)
            
            return None
            
        except (ValueError, AttributeError, IndexError):
            return None

    @staticmethod
    def _validate_coords(lat: float, lng: float) -> Optional[Tuple[float, float]]:
        """
        Validate latitude and longitude ranges.
        
        Args:
            lat: Latitude (-90 to 90)
            lng: Longitude (-180 to 180)
            
        Returns:
            Tuple of (lat, lng) if valid, None otherwise
        """
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return (lat, lng)
        return None

    @staticmethod
    def format_location_name(url: str) -> Optional[str]:
        """
        Extract a location name from a Google Maps URL if available.
        
        Args:
            url: Google Maps URL
            
        Returns:
            Location name or None
        """
        try:
            # Try to extract from /place/LocationName format
            place_match = re.search(r'/place/([^/@]+)', url)
            if place_match:
                location = place_match.group(1)
                # Decode URL encoding and remove coordinates
                location = location.replace('+', ' ')
                location = re.sub(r'/\d+z?$', '', location)
                # Remove coordinates if they're in the name
                location = re.sub(r',\s*[-+]?\d+\.?\d*[,\s]+[-+]?\d+\.?\d*', '', location)
                return location if location and not re.match(r'^[-+]?\d+', location) else None
            
            return None
        except (ValueError, AttributeError):
            return None

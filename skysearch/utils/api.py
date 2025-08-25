"""
API utilities for SkySearch cog
"""

import aiohttp
import discord
from discord.ext import commands
import time
import asyncio
from collections import defaultdict
from typing import Dict, Any


class APIManager:
    """Manages API requests and HTTP client for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
        self.primary_api_url = "https://rest.api.airplanes.live"
        self.fallback_api_url = "https://api.airplanes.live"
        self._http_client = None
        
        # Request tracking statistics - will be loaded from config
        self._request_stats = None
        
        # Hybrid saving configuration
        self._save_counter = 0
        self._save_batch_size = 10  # Save every 10 requests
        self._last_save_time = time.time()
        self._save_interval = 30  # Save every 30 seconds
        
        # Initialize stats asynchronously
        asyncio.create_task(self._initialize_stats())
    
    async def _initialize_stats(self):
        """Initialize statistics from config or use defaults."""
        try:
            # Try to load existing stats from config
            saved_stats = await self.cog.config.api_stats()
            if saved_stats:
                self._request_stats = saved_stats
                # Convert defaultdict back to defaultdict for endpoint_usage
                if 'endpoint_usage' in self._request_stats:
                    self._request_stats['endpoint_usage'] = defaultdict(int, self._request_stats['endpoint_usage'])
                if 'hourly_requests' in self._request_stats:
                    self._request_stats['hourly_requests'] = defaultdict(int, self._request_stats['hourly_requests'])
                if 'daily_requests' in self._request_stats:
                    self._request_stats['daily_requests'] = defaultdict(int, self._request_stats['daily_requests'])
            else:
                # Use default stats if none saved
                self._request_stats = self._get_default_stats()
        except Exception as e:
            print(f"Error loading API stats from config: {e}")
            # Fallback to default stats
            self._request_stats = self._get_default_stats()
    
    def _get_default_stats(self):
        """Get default statistics structure."""
        return {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0,
            'auth_failed_requests': 0,
            'permission_denied_requests': 0,
            'api_mode_usage': {
                'primary': 0,
                'fallback': 0
            },
            'endpoint_usage': defaultdict(int),
            'hourly_requests': defaultdict(int),
            'daily_requests': defaultdict(int),
            'last_request_time': None,
            'total_response_time': 0.0,
            'avg_response_time': 0.0
        }
    
    async def get_api_url(self):
        api_mode = await self.cog.config.api_mode()
        return self.primary_api_url if api_mode == "primary" else self.fallback_api_url

    def get_primary_api_url(self):
        """Get the primary API URL."""
        return self.primary_api_url

    def get_fallback_api_url(self):
        """Get the fallback API URL."""
        return self.fallback_api_url

    async def get_headers(self, url=None, api_mode=None):
        """Return headers with API key for requests, if available. Only send API key for primary API."""
        headers = {}
        api_key = await self.cog.config.airplanesliveapi()
        if api_mode == "primary" and api_key:
            headers['auth'] = api_key
        return headers

    def _update_request_stats(self, api_mode: str, endpoint: str, success: bool, 
                            status_code: int = None, response_time: float = 0.0):
        """Update request statistics."""
        # Ensure stats are initialized
        if self._request_stats is None:
            self._request_stats = self._get_default_stats()
        
        current_time = time.time()
        current_hour = int(current_time // 3600)
        current_day = int(current_time // 86400)
        
        # Basic counters
        self._request_stats['total_requests'] += 1
        if success:
            self._request_stats['successful_requests'] += 1
        else:
            self._request_stats['failed_requests'] += 1
            
            # Specific error counters
            if status_code == 401:
                self._request_stats['auth_failed_requests'] += 1
            elif status_code == 403:
                self._request_stats['permission_denied_requests'] += 1
            elif status_code == 429:
                self._request_stats['rate_limited_requests'] += 1
        
        # API mode usage
        self._request_stats['api_mode_usage'][api_mode] += 1
        
        # Endpoint usage
        self._request_stats['endpoint_usage'][endpoint] += 1
        
        # Time-based tracking
        self._request_stats['hourly_requests'][current_hour] += 1
        self._request_stats['daily_requests'][current_day] += 1
        
        # Response time tracking
        if response_time > 0:
            self._request_stats['total_response_time'] += response_time
            self._request_stats['avg_response_time'] = (
                self._request_stats['total_response_time'] / 
                self._request_stats['total_requests']
            )
        
        self._request_stats['last_request_time'] = current_time
        
        # Hybrid saving: Save on count OR time, whichever comes first
        self._save_counter += 1
        current_time = time.time()
        
        should_save = (
            self._save_counter >= self._save_batch_size or  # Save every N requests
            current_time - self._last_save_time >= self._save_interval  # Save every X seconds
        )
        
        if should_save:
            asyncio.create_task(self._save_stats_to_config())
            self._save_counter = 0
            self._last_save_time = current_time

    def _extract_endpoint(self, url: str) -> str:
        """Extract endpoint name from URL for tracking purposes."""
        # Remove base URLs and query parameters
        for base_url in [self.primary_api_url, self.fallback_api_url]:
            if url.startswith(base_url):
                url = url[len(base_url):]
                break
        
        # Extract the main endpoint path
        if url.startswith('/'):
            url = url[1:]
        
        # Split by '/' and take the first part as endpoint
        endpoint = url.split('/')[0] if url else 'unknown'
        
        # Handle special cases
        if 'find_hex' in url:
            return 'hex_lookup'
        elif 'find_callsign' in url:
            return 'callsign_lookup'
        elif 'find_reg' in url:
            return 'registration_lookup'
        elif 'find_type' in url:
            return 'type_lookup'
        elif 'filter_squawk' in url:
            return 'squawk_filter'
        elif 'filter_mil' in url:
            return 'military_filter'
        elif 'filter_ladd' in url:
            return 'ladd_filter'
        elif 'filter_pia' in url:
            return 'pia_filter'
        elif 'stats' in url:
            return 'stats'
        elif 'v2/' in url:
            return 'v2_endpoint'
        else:
            return endpoint or 'unknown'

    async def _save_stats_to_config(self):
        """Save statistics to Red-DiscordBot config."""
        try:
            if self._request_stats is not None:
                # Convert defaultdict to regular dict for serialization
                stats_to_save = self._request_stats.copy()
                stats_to_save['endpoint_usage'] = dict(stats_to_save['endpoint_usage'])
                stats_to_save['hourly_requests'] = dict(stats_to_save['hourly_requests'])
                stats_to_save['daily_requests'] = dict(stats_to_save['daily_requests'])
                
                await self.cog.config.api_stats.set(stats_to_save)
        except Exception as e:
            print(f"Error saving API stats to config: {e}")

    async def make_request(self, url, ctx=None):
        """Make an HTTP request to the selected API (primary or fallback)."""
        if not self._http_client:
            self._http_client = aiohttp.ClientSession()

        # Determine which API to use
        api_mode = await self.cog.config.api_mode()
        base_url = self.primary_api_url if api_mode == "primary" else self.fallback_api_url
        
        # Extract endpoint for tracking
        original_url = url
        endpoint = self._extract_endpoint(url)

        # Rewrite URL for ICAO hex search if using fallback
        import re
        if api_mode == "fallback":
            # Rewrite to /v2/ endpoints for all supported aircraft lookups
            match = re.search(r"[?&/]find_hex=([0-9a-fA-F]+)", url)
            if match:
                hex_code = match.group(1)
                url = f"{self.fallback_api_url}/v2/hex/{hex_code}"
            else:
                match = re.search(r"[?&/]find_callsign=([A-Za-z0-9]+)", url)
                if match:
                    callsign = match.group(1)
                    url = f"{self.fallback_api_url}/v2/callsign/{callsign}"
                else:
                    match = re.search(r"[?&/]find_reg=([A-Za-z0-9]+)", url)
                    if match:
                        reg = match.group(1)
                        url = f"{self.fallback_api_url}/v2/reg/{reg}"
                    else:
                        match = re.search(r"[?&/]find_type=([A-Za-z0-9]+)", url)
                        if match:
                            typecode = match.group(1)
                            url = f"{self.fallback_api_url}/v2/type/{typecode}"
                        else:
                            match = re.search(r"[?&/]filter_squawk=([0-9]+)", url)
                            if match:
                                squawk = match.group(1)
                                url = f"{self.fallback_api_url}/v2/squawk/{squawk}"
                            elif "filter_mil" in url:
                                url = f"{self.fallback_api_url}/v2/mil"
                            elif "filter_ladd" in url:
                                url = f"{self.fallback_api_url}/v2/ladd"
                            elif "filter_pia" in url:
                                url = f"{self.fallback_api_url}/v2/pia"
                            else:
                                # Otherwise, just replace the base URL
                                url = url.replace(self.primary_api_url, self.fallback_api_url)
        else:
            # If the URL is not absolute, prepend the primary API base URL
            if not url.startswith("https"):
                url = self.primary_api_url + url
            else:
                url = url.replace(self.fallback_api_url, self.primary_api_url)

        start_time = time.time()
        success = False
        status_code = None
        
        try:
            headers = await self.get_headers(url, api_mode)
            async with self._http_client.get(url, headers=headers) as response:
                status_code = response.status
                
                if response.status == 401:
                    error_msg = "API key authentication failed. Please check your API key."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    self._update_request_stats(api_mode, endpoint, False, status_code, time.time() - start_time)
                    return None
                elif response.status == 403:
                    error_msg = "API key does not have permission for this endpoint."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    self._update_request_stats(api_mode, endpoint, False, status_code, time.time() - start_time)
                    return None
                elif response.status == 429:
                    error_msg = "Rate limit exceeded. Please wait before making more requests."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    self._update_request_stats(api_mode, endpoint, False, status_code, time.time() - start_time)
                    return None
                
                response.raise_for_status()
                data = await response.json()
                success = True
                self._update_request_stats(api_mode, endpoint, True, status_code, time.time() - start_time)
                return data
                
        except aiohttp.ClientError as e:
            error_msg = f"Error making request: {e}"
            if ctx:
                await ctx.send(f"❌ **Error:** {error_msg}")
            else:
                print(error_msg)
            self._update_request_stats(api_mode, endpoint, False, status_code, time.time() - start_time)
            return None
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get comprehensive request statistics."""
        # Ensure stats are initialized
        if self._request_stats is None:
            self._request_stats = self._get_default_stats()
        
        stats = self._request_stats.copy()
        
        # Convert defaultdict to regular dict for serialization
        stats['endpoint_usage'] = dict(stats['endpoint_usage'])
        stats['hourly_requests'] = dict(stats['hourly_requests'])
        stats['daily_requests'] = dict(stats['daily_requests'])
        
        # Calculate success rate
        if stats['total_requests'] > 0:
            stats['success_rate'] = (stats['successful_requests'] / stats['total_requests']) * 100
        else:
            stats['success_rate'] = 0.0
        
        # Calculate requests per hour (last 24 hours)
        current_hour = int(time.time() // 3600)
        recent_hours = [current_hour - i for i in range(24)]
        stats['requests_last_24h'] = 0  # Default value
        if stats['hourly_requests']:
            recent_requests = sum(stats['hourly_requests'].get(hour, 0) for hour in recent_hours)
            stats['requests_last_24h'] = recent_requests
        
        # Format last request time
        if stats['last_request_time']:
            stats['last_request_time_formatted'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(stats['last_request_time'])
            )
        
        return stats

    async def wait_for_stats_initialization(self):
        """Wait for statistics to be initialized from config."""
        max_wait = 10  # Maximum seconds to wait
        wait_time = 0
        while self._request_stats is None and wait_time < max_wait:
            await asyncio.sleep(0.1)
            wait_time += 0.1
        
        if self._request_stats is None:
            # If still not initialized, use defaults
            self._request_stats = self._get_default_stats()

    def get_save_config(self):
        """Get current saving configuration."""
        return {
            'batch_size': self._save_batch_size,
            'time_interval': self._save_interval,
            'requests_since_last_save': self._save_counter,
            'seconds_since_last_save': time.time() - self._last_save_time
        }

    def reset_request_stats(self):
        """Reset all request statistics."""
        self._request_stats = self._get_default_stats()
        # Save reset stats to config asynchronously
        asyncio.create_task(self._save_stats_to_config())

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None 

    async def get_stats(self):
        """Fetch stats from the airplanes.live API and return the JSON response or None on error."""
        url = "https://api.airplanes.live/stats"
        if not self._http_client:
            self._http_client = aiohttp.ClientSession()
        try:
            async with self._http_client.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except aiohttp.ClientError as e:
            print(f"Error fetching stats: {e}")
            return None 

    async def get_openweathermap_forecast(self, lat, lon):
        """Fetch 5-day/3-hour forecast from OpenWeatherMap for given lat/lon."""
        api_key = await self.cog.config.openweathermap_api()
        if not api_key:
            return None
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        if not self._http_client:
            self._http_client = aiohttp.ClientSession()
        try:
            async with self._http_client.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return None
        except aiohttp.ClientError as e:
            print(f"Error fetching OpenWeatherMap forecast: {e}")
            return None 
"""
API utilities for SkySearch cog
"""

import aiohttp
import discord
from discord.ext import commands


class APIManager:
    """Manages API requests and HTTP client for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
        self.primary_api_url = "https://rest.api.airplanes.live"
        self.fallback_api_url = "https://api.airplanes.live"
        self._http_client = None
    
    async def get_headers(self, url=None, api_mode=None):
        """Return headers with API key for requests, if available. Only send API key for primary API."""
        headers = {}
        api_key = await self.cog.config.airplanesliveapi()
        if api_mode == "primary" and api_key:
            headers['auth'] = api_key
        return headers

    async def make_request(self, url, ctx=None):
        """Make an HTTP request to the selected API (primary or fallback)."""
        if not self._http_client:
            self._http_client = aiohttp.ClientSession()

        # Determine which API to use
        api_mode = await self.cog.config.api_mode()
        base_url = self.primary_api_url if api_mode == "primary" else self.fallback_api_url

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

        try:
            headers = await self.get_headers(url, api_mode)
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
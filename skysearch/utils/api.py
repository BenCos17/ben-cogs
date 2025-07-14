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
            # If the URL is a find_hex search, rewrite to /hex/[hex]
            match = re.search(r"[?&/]find_hex=([0-9a-fA-F]+)", url)
            if match:
                hex_code = match.group(1)
                url = f"{self.fallback_api_url}/hex/{hex_code}"
            else:
                # Otherwise, just replace the base URL
                url = url.replace(self.primary_api_url, self.fallback_api_url)
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
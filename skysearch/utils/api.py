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
        self.api_url = "https://rest.api.airplanes.live"
        self.fallback_api_url = "https://api.airplanes.live"  # Fallback API URL
        self._http_client = None
    
    async def get_headers(self):
        """Return headers with API key for requests, if available."""
        headers = {}
        api_key = await self.cog.config.airplanesliveapi()
        if api_key:
            headers['auth'] = api_key  # Use 'auth' header as specified in API docs
        return headers

    async def make_request(self, url, ctx=None, use_fallback=False):
        """Make an HTTP request to the API, with fallback to secondary API if the primary fails."""
        if not self._http_client:
            self._http_client = aiohttp.ClientSession()
        
        try:
            headers = await self.get_headers()  # Get headers with API key if available
            
            async with self._http_client.get(url, headers=headers) as response:
                if response.status == 401:
                    error_msg = "API key authentication failed. Please check your API key."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    # Fallback if not already tried
                    if not use_fallback and self.fallback_api_url in url or self.api_url in url:
                        fallback_url = url.replace(self.api_url, self.fallback_api_url)
                        return await self.make_request(fallback_url, ctx, use_fallback=True)
                    return None
                elif response.status == 403:
                    error_msg = "API key does not have permission for this endpoint."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    # Fallback if not already tried
                    if not use_fallback and self.fallback_api_url in url or self.api_url in url:
                        fallback_url = url.replace(self.api_url, self.fallback_api_url)
                        return await self.make_request(fallback_url, ctx, use_fallback=True)
                    return None
                elif response.status == 429:
                    error_msg = "Rate limit exceeded. Please wait before making more requests."
                    if ctx:
                        await ctx.send(f"❌ **Error:** {error_msg}")
                    else:
                        print(error_msg)
                    # Fallback if not already tried
                    if not use_fallback and self.fallback_api_url in url or self.api_url in url:
                        fallback_url = url.replace(self.api_url, self.fallback_api_url)
                        return await self.make_request(fallback_url, ctx, use_fallback=True)
                    return None
                elif response.status >= 500:
                    # Server error, try fallback if not already tried
                    if not use_fallback and self.api_url in url:
                        fallback_url = url.replace(self.api_url, self.fallback_api_url)
                        return await self.make_request(fallback_url, ctx, use_fallback=True)
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            error_msg = f"Error making request: {e}"
            if ctx:
                await ctx.send(f"❌ **Error:** {error_msg}")
            else:
                print(error_msg)
            # Fallback if not already tried
            if not use_fallback and self.api_url in url:
                fallback_url = url.replace(self.api_url, self.fallback_api_url)
                return await self.make_request(fallback_url, ctx, use_fallback=True)
            return None
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None 
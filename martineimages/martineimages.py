from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
import discord
import aiohttp
import json
import logging
from typing import Optional

log = logging.getLogger("red.cogs.martineimages")

class MartineImages(commands.Cog):
    """Cog for Martine Images API."""

    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://api.martinebot.com/v1"
        self.session = None

    async def cog_load(self):
        """Initialize the cog and create aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cog_unload(self):
        """Clean up the cog and close aiohttp session"""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def fetch_image(self, endpoint: str, params: Optional[dict] = None) -> Optional[str]:
        await self._ensure_session()
        headers = {"User-Agent": "Red-MartineImages/ben-cogs/v1.1.4"}
        params = params or {}
        try:
            async with self.session.get(
                f"{self.base_url}{endpoint}", headers=headers, params=params
            ) as resp:
                if resp.status == 200:
                    try:
                        json_data = await resp.json()
                        # If endpoint returns plain string, not JSON
                        if isinstance(json_data, str):
                            return json_data
                        # Try different possible response formats
                        if isinstance(json_data, dict):
                            return json_data.get("url") or json_data.get("image") or json_data.get("link")
                        return None
                    except aiohttp.ContentTypeError:
                        # If response is not JSON, try reading as text
                        text = await resp.text()
                        if text:
                            return text
                        return None
                else:
                    log.warning(f"Martine API returned status {resp.status} for {endpoint}")
                    return None
        except aiohttp.ClientError as e:
            log.error(f"Error fetching from Martine API: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error in fetch_image: {e}", exc_info=True)
            return None

    @commands.command(name="martinememe")
    async def meme(self, ctx: commands.Context):
        """Get a random meme from Martine API."""
        url = await self.fetch_image("/images/memes")
        if url:
            await ctx.send(url)
        else:
            await ctx.send("Couldn't fetch a meme at this time.")

    @commands.command(name="martinewallpaper")
    async def wallpaper(self, ctx: commands.Context):
        """Get a random wallpaper from Martine API."""
        url = await self.fetch_image("/images/wallpaper")
        if url:
            await ctx.send(url)
        else:
            await ctx.send("Couldn't fetch a wallpaper at this time.")

    @commands.command(name="martinesubreddit")
    async def subreddit(self, ctx: commands.Context, subreddit: str):
        """Get a random image from a specified subreddit using Martine API."""
        url = await self.fetch_image("/images/subreddit", {"subreddit": subreddit})
        if url:
            await ctx.send(url)
        else:
            await ctx.send(f"Couldn't fetch an image from r/{subreddit}.")

    @commands.command(name="martineship")
    async def ship(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """Generate a ship image with two Discord users using Martine API."""
        url = await self.fetch_image(
            "/imagesgen/ship", {"user1": str(user1.id), "user2": str(user2.id)}
        )
        if url:
            await ctx.send(url)
        else:
            await ctx.send("Couldn't generate a ship image at this time.")

    @commands.command(name="martineosuprofile")
    async def osuprofile(self, ctx: commands.Context, username: str):
        """Generate an osu! profile card using Martine API."""
        url = await self.fetch_image("/imagesgen/osuprofile", {"username": username})
        if url:
            await ctx.send(url)
        else:
            await ctx.send(f"Couldn't fetch osu! profile for **{username}**.")

    @commands.command(name="martinedebug")
    @commands.is_owner()
    async def debug_api(self, ctx: commands.Context, endpoint: str = "/images/memes"):
        """Debug command to inspect API responses. Owner only."""
        await self._ensure_session()
        headers = {"User-Agent": "Red-MartineImages/ben-cogs/v1.1.4"}
        full_url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.get(full_url, headers=headers) as resp:
                status = resp.status
                content_type = resp.headers.get("Content-Type", "unknown")
                
                # Try to get response as text first
                try:
                    text_response = await resp.text()
                except:
                    text_response = "Could not read as text"
                
                # Try to get as JSON
                json_response = None
                try:
                    await resp.rewind()  # Reset response stream
                    json_response = await resp.json()
                except:
                    pass
                
                # Build debug message
                debug_msg = f"**API Debug Info**\n"
                debug_msg += f"URL: `{full_url}`\n"
                debug_msg += f"Status: `{status}`\n"
                debug_msg += f"Content-Type: `{content_type}`\n\n"
                
                if json_response:
                    debug_msg += f"**JSON Response:**\n```json\n{json.dumps(json_response, indent=2)[:1500]}\n```\n"
                
                if text_response and not json_response:
                    debug_msg += f"**Text Response (first 500 chars):**\n```\n{text_response[:500]}\n```\n"
                
                # Split into multiple messages if too long
                for page in pagify(debug_msg):
                    await ctx.send(page)
                    
        except Exception as e:
            await ctx.send(f"**Error:** {type(e).__name__}: {str(e)}")
            log.error(f"Debug command error: {e}", exc_info=True)




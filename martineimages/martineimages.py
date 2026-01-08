from redbot.core import commands
import discord
import aiohttp
from typing import Optional

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
        async with self.session.get(
            f"{self.base_url}{endpoint}", headers=headers, params=params
        ) as resp:
            if resp.status == 200:
                json = await resp.json()
                # If endpoint returns plain string, not JSON
                if isinstance(json, str):
                    return json
                return json.get("url")
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




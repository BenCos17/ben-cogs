"""
XKCD Comic Lookup Cog for Red Discord Bot

This cog provides commands to search and display XKCD comics.
Commands:
- [p]xkcd <number> - Get a specific comic by number
- [p]xkcd random - Get a random comic
- [p]xkcd latest - Get the latest comic
- [p]xkcd search <query> - Search comics by title/alt text
"""

import discord
import aiohttp
import random
from typing import Optional
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class XKCD(commands.Cog):
    """XKCD Comic Lookup Cog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
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
    
    async def get_comic(self, comic_id: Optional[int] = None) -> Optional[dict]:
        """Fetch a comic from the XKCD API"""
        await self._ensure_session()
        
        if comic_id is None:
            url = "https://xkcd.com/info.0.json"
        else:
            url = f"https://xkcd.com/{comic_id}/info.0.json"
            
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"Error fetching comic: {e}")
            return None
    
    async def search_comics(self, query: str) -> list:
        """Search comics by title and alt text"""
        # This is a simplified search since XKCD doesn't have a search API
        # We'll search through recent comics and check titles/alt text
        results = []
        query_lower = query.lower()
        
        # Get the latest comic number
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        
        # Search through the last 100 comics
        search_range = min(100, latest_num)
        for i in range(latest_num, max(0, latest_num - search_range), -1):
            comic = await self.get_comic(i)
            if comic:
                title_lower = comic.get('title', '').lower()
                alt_lower = comic.get('alt', '').lower()
                
                if query_lower in title_lower or query_lower in alt_lower:
                    results.append(comic)
                    
                # Limit results to prevent spam
                if len(results) >= 10:
                    break
                    
        return results
    
    def create_embed(self, comic: dict) -> discord.Embed:
        """Create a Discord embed for the comic"""
        embed = discord.Embed(
            title=f"XKCD #{comic['num']}: {comic['title']}",
            description=comic.get('alt', ''),
            url=f"https://xkcd.com/{comic['num']}/",
            color=discord.Color.blue()
        )
        
        embed.set_image(url=comic['img'])
        embed.set_footer(text=f"Published: {comic['year']}-{comic['month']:02d}-{comic['day']:02d}")
        
        return embed
    
    @commands.command(name="xkcd")
    async def xkcd_command(self, ctx, *, query: str = "latest"):
        """Get XKCD comics by number, random, latest, or search"""
        async with ctx.typing():
            if query.lower() == "random":
                # Get random comic
                latest = await self.get_comic()
                if not latest:
                    await ctx.send("❌ Failed to fetch latest comic information.")
                    return
                    
                random_num = random.randint(1, latest['num'])
                comic = await self.get_comic(random_num)
                if comic:
                    embed = self.create_embed(comic)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Failed to fetch random comic.")
                    
            elif query.lower() == "latest":
                # Get latest comic
                comic = await self.get_comic()
                if comic:
                    embed = self.create_embed(comic)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Failed to fetch latest comic.")
                    
            elif query.isdigit():
                # Get specific comic by number
                comic_num = int(query)
                comic = await self.get_comic(comic_num)
                if comic:
                    embed = self.create_embed(comic)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ Comic #{comic_num} not found.")
                    
            else:
                # Search comics
                results = await self.search_comics(query)
                if results:
                    if len(results) == 1:
                        # Single result, show directly
                        embed = self.create_embed(results[0])
                        await ctx.send(embed=embed)
                    else:
                        # Multiple results, show menu
                        embeds = [self.create_embed(comic) for comic in results]
                        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=60)
                else:
                    await ctx.send(f"❌ No comics found matching '{query}'.")
    
    @xkcd_command.error
    async def xkcd_error(self, ctx, error):
        """Handle errors in the xkcd command"""
        if isinstance(error, commands.CommandInvokeError):
            original_error = error.original
            error_msg = f"❌ An error occurred: {type(original_error).__name__}: {str(original_error)}"
            await ctx.send(error_msg)
        else:
            await ctx.send("❌ Invalid input. Use a number, 'random', 'latest', or search terms.")

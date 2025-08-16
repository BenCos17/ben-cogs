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
        
        # Handle date formatting - XKCD API returns strings, not integers
        year = comic.get('year', '')
        month = comic.get('month', '')
        day = comic.get('day', '')
        
        if year and month and day:
            # Try to format as date if possible, otherwise use as-is
            try:
                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                date_str = f"{year}-{month}-{day}"
        else:
            date_str = "Unknown date"
            
        embed.set_footer(text=f"Published: {date_str}")
        
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
    
    @commands.command(name="xkcddate")
    async def xkcd_date_command(self, ctx, *, date_query: str):
        """Search XKCD comics by date. Use formats like: 2023, 2023-12, 2023-12-25"""
        async with ctx.typing():
            results = await self.search_by_date(date_query)
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
                await ctx.send(f"❌ No comics found for date '{date_query}'.")
    
    async def search_by_date(self, date_query: str) -> list:
        """Search comics by date"""
        results = []
        date_parts = date_query.split('-')
        
        if len(date_parts) == 1:
            # Just year: 2023
            year = date_parts[0]
            if not year.isdigit() or len(year) != 4:
                return results
            results = await self._search_by_year(int(year))
            
        elif len(date_parts) == 2:
            # Year and month: 2023-12
            year, month = date_parts
            if not year.isdigit() or not month.isdigit() or len(year) != 4 or len(month) != 2:
                return results
            results = await self._search_by_year_month(int(year), int(month))
            
        elif len(date_parts) == 3:
            # Full date: 2023-12-25
            year, month, day = date_parts
            if not year.isdigit() or not month.isdigit() or not day.isdigit():
                return results
            if len(year) != 4 or len(month) != 2 or len(day) != 2:
                return results
            results = await self._search_by_exact_date(int(year), int(month), int(day))
            
        return results
    
    async def _search_by_year(self, year: int) -> list:
        """Search comics by year"""
        results = []
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        # Search through all comics for the year
        for i in range(1, latest_num + 1):
            comic = await self.get_comic(i)
            if comic and str(comic.get('year', '')) == str(year):
                results.append(comic)
                if len(results) >= 20:  # Limit results
                    break
        return results
    
    async def _search_by_year_month(self, year: int, month: int) -> list:
        """Search comics by year and month"""
        results = []
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        # Search through all comics for the year/month
        for i in range(1, latest_num + 1):
            comic = await self.get_comic(i)
            if (comic and 
                str(comic.get('year', '')) == str(year) and 
                str(comic.get('month', '')).zfill(2) == str(month).zfill(2)):
                results.append(comic)
                if len(results) >= 20:  # Limit results
                    break
        return results
    
    async def _search_by_exact_date(self, year: int, month: int, day: int) -> list:
        """Search comics by exact date"""
        results = []
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        # Search through all comics for the exact date
        for i in range(1, latest_num + 1):
            comic = await self.get_comic(i)
            if (comic and 
                str(comic.get('year', '')) == str(year) and 
                str(comic.get('month', '')).zfill(2) == str(month).zfill(2) and
                str(comic.get('day', '')).zfill(2) == str(day).zfill(2)):
                results.append(comic)
                break  # Should only be one comic per day
        
        return results
    
    @xkcd_command.error
    async def xkcd_error(self, ctx, error):
        """Handle errors in the xkcd command"""
        if isinstance(error, commands.CommandInvokeError):
            original_error = error.original
            error_msg = f"❌ An error occurred: {type(original_error).__name__}: {str(original_error)}"
            await ctx.send(error_msg)
        else:
            await ctx.send("❌ Invalid input. Use a number, 'random', 'latest', or search terms.")

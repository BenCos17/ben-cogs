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
import time
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
        self.comic_cache = {}  # Cache for comics to avoid repeated API calls
        self.cache_timeout = 300  # 5 minutes cache timeout
        
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
        """Fetch a comic from the XKCD API with caching"""
        await self._ensure_session()
        
        # Check cache first
        if comic_id is not None and comic_id in self.comic_cache:
            cached_data = self.comic_cache[comic_id]
            if cached_data['timestamp'] + self.cache_timeout > time.time():
                return cached_data['comic']
            else:
                # Remove expired cache entry
                del self.comic_cache[comic_id]
        
        if comic_id is None:
            url = "https://xkcd.com/info.0.json"
        else:
            url = f"https://xkcd.com/{comic_id}/info.0.json"
            
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    comic_data = await response.json()
                    
                    # Cache the result
                    if comic_id is not None:
                        self.comic_cache[comic_id] = {
                            'comic': comic_data,
                            'timestamp': time.time()
                        }
                    
                    return comic_data
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
    
    async def search_by_title(self, title_query: str) -> list:
        """Search comics by title using archive page for better performance"""
        results = []
        query_lower = title_query.lower().strip()
        
        try:
            # Use XKCD's archive page instead of individual API calls
            async with self.session.get("https://xkcd.com/archive/") as response:
                if response.status == 200:
                    html = await response.text()
                    # Parse the archive page to find comics by title
                    import re
                    # Look for comic links with titles
                    pattern = r'<a href="/(\d+)/">(\d{4}-\d{2}-\d{2})</a>'
                    matches = re.findall(pattern, html)
                    
                    # Get comics and check titles
                    for comic_num, date_str in matches:
                        comic = await self.get_comic(int(comic_num))
                        if comic:
                            title_lower = comic.get('title', '').lower()
                            alt_lower = comic.get('alt', '').lower()
                            
                            # Check if query is in title or alt text
                            if (query_lower in title_lower or 
                                query_lower in alt_lower or
                                any(word in title_lower for word in query_lower.split())):
                                results.append(comic)
                                if len(results) >= 15:  # Limit results
                                    break
        except Exception as e:
            print(f"Error searching archive by title: {e}")
            # Fallback to old method if archive fails
            results = await self._search_by_title_fallback(title_query)
        
        return results
    
    async def _search_by_title_fallback(self, title_query: str) -> list:
        """Fallback method for title search"""
        results = []
        query_lower = title_query.lower().strip()
        
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        # Search through last 200 comics as fallback
        for i in range(latest_num, max(0, latest_num - 200), -1):
            comic = await self.get_comic(i)
            if comic:
                title_lower = comic.get('title', '').lower()
                alt_lower = comic.get('alt', '').lower()
                
                # Check if query is in title or alt text
                if (query_lower in title_lower or 
                    query_lower in alt_lower or
                    any(word in title_lower for word in query_lower.split())):
                    results.append(comic)
                    if len(results) >= 15:
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
        """Search XKCD comics by date. Use formats like: 2023, 2023-12, 2023-12-25, december 2023"""
        try:
            async with ctx.typing():
                # Add a timeout to prevent hanging
                import asyncio
                results = await asyncio.wait_for(self.search_by_date(date_query), timeout=30.0)
                
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
                    help_text = (
                        f"❌ No comics found for '{date_query}'.\n\n"
                        "**Supported formats:**\n"
                        "• `2023` - All comics from 2023\n"
                        "• `2023-12` - All comics from December 2023\n"
                        "• `december 2023` - All comics from December 2023\n"
                        "• `2023-12-25` - Comic from December 25, 2023"
                    )
                    await ctx.send(help_text)
        except asyncio.TimeoutError:
            await ctx.send("❌ Search timed out. Please try a more specific search or try again later.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred during search: {str(e)}")
    
    @commands.command(name="xkcdtitle")
    async def xkcd_title_command(self, ctx, *, title_query: str):
        """Search XKCD comics by title/cartoon name"""
        try:
            async with ctx.typing():
                import asyncio
                results = await asyncio.wait_for(self.search_by_title(title_query), timeout=30.0)
                
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
                    await ctx.send(f"❌ No comics found with title containing '{title_query}'.")
        except asyncio.TimeoutError:
            await ctx.send("❌ Search timed out. Please try a more specific search or try again later.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred during search: {str(e)}")
    
    async def search_by_date(self, date_query: str) -> list:
        """Search comics by date"""
        results = []
        
        # Handle natural language formats
        date_query_lower = date_query.lower().strip()
        
        # Try to parse natural language first
        if any(word in date_query_lower for word in ['january', 'february', 'march', 'april', 'may', 'june', 
                                                    'july', 'august', 'september', 'october', 'november', 'december']):
            results = await self._parse_natural_language_date(date_query_lower)
            if results:
                return results
        
        # Fall back to standard format parsing
        date_parts = date_query.split('-')
        
        if len(date_parts) == 1:
            # Just year: 2023
            year = date_parts[0].strip()
            if not year.isdigit() or len(year) != 4:
                return results
            results = await self._search_by_year(int(year))
            
        elif len(date_parts) == 2:
            # Year and month: 2023-12 or 12-2023
            part1, part2 = date_parts[0].strip(), date_parts[1].strip()
            
            if len(part1) == 4 and part1.isdigit() and len(part2) <= 2 and part2.isdigit():
                # Format: 2023-12
                results = await self._search_by_year_month(int(part1), int(part2))
            elif len(part2) == 4 and part2.isdigit() and len(part1) <= 2 and part1.isdigit():
                # Format: 12-2023
                results = await self._search_by_year_month(int(part2), int(part1))
            
        elif len(date_parts) == 3:
            # Full date: 2023-12-25
            year, month, day = date_parts[0].strip(), date_parts[1].strip(), date_parts[2].strip()
            if not year.isdigit() or not month.isdigit() or not day.isdigit():
                return results
            if len(year) != 4 or len(month) != 2 or len(day) != 2:
                return results
            results = await self._search_by_exact_date(int(year), int(month), int(day))
            
        return results
    
    async def _parse_natural_language_date(self, date_query: str) -> list:
        """Parse natural language date queries like 'december 2023'"""
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        words = date_query.split()
        year = None
        month = None
        
        for word in words:
            if word in month_map:
                month = month_map[word]
            elif word.isdigit() and len(word) == 4:
                year = int(word)
        
        if year and month:
            return await self._search_by_year_month(year, month)
        elif year:
            return await self._search_by_year(year)
        
        return []
    
    async def _search_by_year(self, year: int) -> list:
        """Search comics by year using archive page for better performance"""
        results = []
        try:
            # Use XKCD's archive page instead of individual API calls
            async with self.session.get("https://xkcd.com/archive/") as response:
                if response.status == 200:
                    html = await response.text()
                    # Parse the archive page to find comics from specific year
                    import re
                    # Look for comic links with dates
                    pattern = r'<a href="/(\d+)/">(\d{4}-\d{2}-\d{2})</a>'
                    matches = re.findall(pattern, html)
                    
                    for comic_num, date_str in matches:
                        if date_str.startswith(str(year)):
                            comic = await self.get_comic(int(comic_num))
                            if comic:
                                results.append(comic)
                                if len(results) >= 20:
                                    break
        except Exception as e:
            print(f"Error searching archive: {e}")
            # Fallback to old method if archive fails
            results = await self._search_by_year_fallback(year)
        
        return results
    
    async def _search_by_year_fallback(self, year: int) -> list:
        """Fallback method for year search"""
        results = []
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        # Only search last 200 comics as fallback
        for i in range(latest_num, max(0, latest_num - 200), -1):
            comic = await self.get_comic(i)
            if comic and str(comic.get('year', '')) == str(year):
                results.append(comic)
                if len(results) >= 20:
                    break
        return results
    
    async def _search_by_year_month(self, year: int, month: int) -> list:
        """Search comics by year and month - optimized to search recent comics first"""
        results = []
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        # Start from recent comics and work backwards for better performance
        for i in range(latest_num, max(0, latest_num - 500), -1):
            comic = await self.get_comic(i)
            if (comic and 
                str(comic.get('year', '')) == str(year) and 
                str(comic.get('month', '')).zfill(2) == str(month).zfill(2)):
                results.append(comic)
                if len(results) >= 20:  # Limit results
                    break
        return results
    
    async def _search_by_exact_date(self, year: int, month: int, day: int) -> list:
        """Search comics by exact date - optimized to search recent comics first"""
        results = []
        latest = await self.get_comic()
        if not latest:
            return results
            
        latest_num = latest['num']
        # Start from recent comics and work backwards for better performance
        for i in range(latest_num, max(0, latest_num - 500), -1):
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

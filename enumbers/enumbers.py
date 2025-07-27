import discord
from redbot.core import commands, Config
import aiohttp
import difflib
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger("red.cogs.enumbers")

class Enumbers(commands.Cog):
    """Look up E-numbers (food additives) using the enumbers API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        self.api_url = "https://enumbers.jarvisdiscordbot.net/api/enumbers"
        self.recent_searches = []  # Store recent searches for the session
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = timedelta(minutes=30)  # Cache for 30 minutes
        self._session = None

    async def cog_unload(self):
        """Clean up resources when cog is unloaded."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def fetch_enumbers(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch E-numbers data with caching."""
        # Check if we have valid cached data
        if (self._cache and self._cache_timestamp and 
            datetime.now() - self._cache_timestamp < self._cache_duration):
            return self._cache

        try:
            session = await self.get_session()
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; Discordbot/1.0; +https://discordapp.com)",
                "Accept": "application/json"
            }
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            
            async with session.get(self.api_url, headers=headers, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Cache the data
                    self._cache = data
                    self._cache_timestamp = datetime.now()
                    return data
                else:
                    logger.error(f"API returned status {resp.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error("API request timed out")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data: {e}")
            return None

    def normalize_code(self, code: str) -> str:
        """Normalize E-number code format."""
        code = code.upper().replace(" ", "").replace("-", "")
        if not code.startswith("E"):
            code = "E" + code
        return code

    def create_enumber_embed(self, code: str, data: Dict[str, Any]) -> discord.Embed:
        """Create a rich embed for E-number display."""
        name = data.get("name", "Unknown")
        url = data.get("openfoodfacts_url")
        additive = data.get("openfoodfacts_additive")
        
        # Determine color based on E-number range
        try:
            num = int(code[1:])
            if num < 100:
                color = discord.Color.green()  # Natural colors
            elif num < 200:
                color = discord.Color.blue()   # Preservatives
            elif num < 300:
                color = discord.Color.yellow() # Antioxidants
            elif num < 400:
                color = discord.Color.orange() # Thickeners
            elif num < 500:
                color = discord.Color.red()    # Acidity regulators
            elif num < 600:
                color = discord.Color.purple() # Flavor enhancers
            else:
                color = discord.Color.dark_grey() # Others
        except (ValueError, IndexError):
            color = discord.Color.green()

        embed = discord.Embed(
            title=f"🔬 {code}: {name}",
            description=f"**{name}**",
            color=color,
            timestamp=datetime.now()
        )
        
        # Add fields with better formatting
        if url:
            embed.add_field(
                name="📋 OpenFoodFacts", 
                value=f"[View Details]({url})", 
                inline=True
            )
        
        if additive:
            add_name = additive.get("name")
            add_url = additive.get("url")
            wikidata = additive.get("sameAs", [])
            
            if add_name:
                embed.add_field(
                    name="🧪 Additive Name", 
                    value=add_name, 
                    inline=True
                )
            
            if add_url:
                embed.add_field(
                    name="ℹ️ More Information", 
                    value=f"[Learn More]({add_url})", 
                    inline=True
                )
            
            if wikidata:
                wikidata_links = "\n".join(f"• [Wikidata]({link})" for link in wikidata[:3])
                if len(wikidata) > 3:
                    wikidata_links += f"\n...and {len(wikidata) - 3} more"
                embed.add_field(
                    name="📚 Wikidata References", 
                    value=wikidata_links, 
                    inline=False
                )

        embed.set_footer(text="E-numbers Database | Use !enumbersearch for partial matches")
        return embed

    def get_suggestions(self, code: str, data: List[Dict[str, Any]]) -> List[str]:
        """Get fuzzy match suggestions for an E-number."""
        codes = [item.get("code", "") for item in data]
        names = [item.get("name", "") for item in data]
        
        # Direct substring matches
        direct_matches = [c for c in codes if code in c.upper()]
        
        # Fuzzy matches
        close_codes = difflib.get_close_matches(code, codes, n=3, cutoff=0.6)
        close_names = difflib.get_close_matches(code, names, n=3, cutoff=0.6)
        
        # Combine and deduplicate
        suggestions = direct_matches + close_codes + close_names
        return list(dict.fromkeys(suggestions))[:5]

    @commands.command(name="enumber", aliases=["en"])
    async def enumber(self, ctx, *, code: str):
        """Look up an E-number (e.g. E621, E100, E950).
        
        You can type E-numbers with or without spaces, e.g. E120, e 120, or E  1 2 0.
        """
        async with ctx.typing():
            code = self.normalize_code(code)
            
            data = await self.fetch_enumbers()
            if data is None:
                embed = discord.Embed(
                    title="❌ API Error",
                    description="Could not reach the E-numbers API. Please try again later.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Find exact match
            found = None
            for item in data:
                if item.get("code", "").upper() == code:
                    found = item
                    break

            if not found:
                # Get suggestions
                suggestions = self.get_suggestions(code, data)
                
                embed = discord.Embed(
                    title="❌ E-number Not Found",
                    description=f"E-number `{code}` was not found in the database.",
                    color=discord.Color.red()
                )
                
                if suggestions:
                    embed.add_field(
                        name="💡 Did you mean?",
                        value=", ".join(f"`{s}`" for s in suggestions),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                return

            # Add to recent searches
            self.recent_searches.insert(0, found.get("code", code))
            self.recent_searches = self.recent_searches[:10]  # Keep only 10 most recent

            # Create and send embed
            embed = self.create_enumber_embed(code, found)
            await ctx.send(embed=embed)

    @commands.command(name="enumbersearch", aliases=["esearch"])
    async def enumbersearch(self, ctx, *, query: str):
        """Search for E-numbers by code or name (partial/fuzzy matching).
        
        Examples:
        - !esearch 621 (finds E621)
        - !esearch aspartame (finds E951)
        - !esearch color (finds color additives)
        """
        async with ctx.typing():
            data = await self.fetch_enumbers()
            if data is None:
                embed = discord.Embed(
                    title="❌ API Error",
                    description="Could not reach the E-numbers API. Please try again later.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            query = query.upper().replace(" ", "")
            
            # Find matches
            matches = []
            for item in data:
                code = item.get("code", "").upper()
                name = item.get("name", "").upper()
                if query in code or query in name:
                    matches.append(item)

            if not matches:
                # Try fuzzy matching
                suggestions = self.get_suggestions(query, data)
                
                embed = discord.Embed(
                    title="🔍 No Direct Matches Found",
                    description=f"No E-numbers found matching '{query}'.",
                    color=discord.Color.orange()
                )
                
                if suggestions:
                    embed.add_field(
                        name="💡 Similar results:",
                        value=", ".join(f"`{s}`" for s in suggestions),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                return

            # Create results embed
            embed = discord.Embed(
                title=f"🔍 Search Results for '{query}'",
                description=f"Found {len(matches)} matching E-number(s):",
                color=discord.Color.blue()
            )

            # Show first 10 results
            for i, item in enumerate(matches[:10], 1):
                code = item.get("code", "?")
                name = item.get("name", "?")
                embed.add_field(
                    name=f"{i}. {code}",
                    value=name,
                    inline=True
                )

            if len(matches) > 10:
                embed.add_field(
                    name="📄 More Results",
                    value=f"...and {len(matches) - 10} more. Refine your search for fewer results.",
                    inline=False
                )

            await ctx.send(embed=embed)

    @commands.command(name="enumberlist", aliases=["elist"])
    async def enumberlist(self, ctx, page: int = 1):
        """List all E-numbers with pagination (20 per page).
        
        Use the buttons to navigate through pages.
        """
        async with ctx.typing():
            data = await self.fetch_enumbers()
            if data is None:
                embed = discord.Embed(
                    title="❌ API Error",
                    description="Could not reach the E-numbers API. Please try again later.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            per_page = 20
            total = len(data)
            pages = (total + per_page - 1) // per_page
            page = max(1, min(page, pages))

            def make_page_embed(page_num: int) -> discord.Embed:
                start = (page_num - 1) * per_page
                end = start + per_page
                
                embed = discord.Embed(
                    title="📋 E-numbers Database",
                    description=f"Page {page_num}/{pages} • Total: {total} E-numbers",
                    color=discord.Color.blue()
                )
                
                # Group by first digit for better organization
                page_data = data[start:end]
                current_group = None
                group_items = []
                
                for item in page_data:
                    code = item.get("code", "")
                    name = item.get("name", "")
                    
                    try:
                        group = code[1] if len(code) > 1 else "0"
                    except (IndexError, ValueError):
                        group = "0"
                    
                    if group != current_group:
                        if group_items:
                            embed.add_field(
                                name=f"E{current_group}xx Series",
                                value="\n".join(group_items),
                                inline=False
                            )
                        current_group = group
                        group_items = []
                    
                    group_items.append(f"`{code}`: {name}")
                
                if group_items:
                    embed.add_field(
                        name=f"E{current_group}xx Series",
                        value="\n".join(group_items),
                        inline=False
                    )
                
                return embed

            class EnumberListView(discord.ui.View):
                def __init__(self, cog, ctx, total_pages, current_page):
                    super().__init__(timeout=120)  # 2 minute timeout
                    self.cog = cog
                    self.ctx = ctx
                    self.total_pages = total_pages
                    self.current_page = current_page
                    self.message = None
                    self.update_buttons()

                def update_buttons(self):
                    self.clear_items()
                    
                    # First page button
                    self.add_item(self.FirstButton(self))
                    # Previous button
                    self.add_item(self.PreviousButton(self))
                    # Page indicator
                    self.add_item(self.PageButton(self))
                    # Next button
                    self.add_item(self.NextButton(self))
                    # Last page button
                    self.add_item(self.LastButton(self))

                class FirstButton(discord.ui.Button):
                    def __init__(self, parent):
                        super().__init__(
                            label="⏮️ First",
                            style=discord.ButtonStyle.secondary,
                            disabled=parent.current_page <= 1
                        )
                        self.parent = parent

                    async def callback(self, interaction: discord.Interaction):
                        if interaction.user != self.parent.ctx.author:
                            await interaction.response.send_message(
                                "❌ You can't control this pagination.", 
                                ephemeral=True
                            )
                            return
                        
                        if self.parent.current_page > 1:
                            self.parent.current_page = 1
                            await self.parent.update_message(interaction)

                class PreviousButton(discord.ui.Button):
                    def __init__(self, parent):
                        super().__init__(
                            label="◀️ Previous",
                            style=discord.ButtonStyle.primary,
                            disabled=parent.current_page <= 1
                        )
                        self.parent = parent

                    async def callback(self, interaction: discord.Interaction):
                        if interaction.user != self.parent.ctx.author:
                            await interaction.response.send_message(
                                "❌ You can't control this pagination.", 
                                ephemeral=True
                            )
                            return
                        
                        if self.parent.current_page > 1:
                            self.parent.current_page -= 1
                            await self.parent.update_message(interaction)

                class PageButton(discord.ui.Button):
                    def __init__(self, parent):
                        super().__init__(
                            label=f"📄 {parent.current_page}/{parent.total_pages}",
                            style=discord.ButtonStyle.secondary,
                            disabled=True
                        )
                        self.parent = parent

                class NextButton(discord.ui.Button):
                    def __init__(self, parent):
                        super().__init__(
                            label="Next ▶️",
                            style=discord.ButtonStyle.primary,
                            disabled=parent.current_page >= parent.total_pages
                        )
                        self.parent = parent

                    async def callback(self, interaction: discord.Interaction):
                        if interaction.user != self.parent.ctx.author:
                            await interaction.response.send_message(
                                "❌ You can't control this pagination.", 
                                ephemeral=True
                            )
                            return
                        
                        if self.parent.current_page < self.parent.total_pages:
                            self.parent.current_page += 1
                            await self.parent.update_message(interaction)

                class LastButton(discord.ui.Button):
                    def __init__(self, parent):
                        super().__init__(
                            label="Last ⏭️",
                            style=discord.ButtonStyle.secondary,
                            disabled=parent.current_page >= parent.total_pages
                        )
                        self.parent = parent

                    async def callback(self, interaction: discord.Interaction):
                        if interaction.user != self.parent.ctx.author:
                            await interaction.response.send_message(
                                "❌ You can't control this pagination.", 
                                ephemeral=True
                            )
                            return
                        
                        if self.parent.current_page < self.parent.total_pages:
                            self.parent.current_page = self.parent.total_pages
                            await self.parent.update_message(interaction)

                async def update_message(self, interaction):
                    self.update_buttons()
                    embed = make_page_embed(self.current_page)
                    await interaction.response.edit_message(embed=embed, view=self)

                async def on_timeout(self):
                    for item in self.children:
                        item.disabled = True
                    if self.message:
                        try:
                            await self.message.edit(view=self)
                        except Exception:
                            pass

            view = EnumberListView(self, ctx, pages, page)
            embed = make_page_embed(page)
            view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="enumbercount", aliases=["ecount"])
    async def enumbercount(self, ctx):
        """Show statistics about the E-numbers database."""
        async with ctx.typing():
            data = await self.fetch_enumbers()
            if data is None:
                embed = discord.Embed(
                    title="❌ API Error",
                    description="Could not reach the E-numbers API. Please try again later.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Calculate statistics
            total = len(data)
            
            # Count by series
            series_counts = {}
            for item in data:
                code = item.get("code", "")
                try:
                    series = code[1] if len(code) > 1 else "0"
                    series_counts[series] = series_counts.get(series, 0) + 1
                except (IndexError, ValueError):
                    series_counts["0"] = series_counts.get("0", 0) + 1

            embed = discord.Embed(
                title="📊 E-numbers Database Statistics",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📈 Total E-numbers",
                value=f"**{total:,}**",
                inline=True
            )
            
            # Show series breakdown
            series_text = ""
            for series in sorted(series_counts.keys()):
                count = series_counts[series]
                percentage = (count / total) * 100
                series_text += f"E{series}xx: {count} ({percentage:.1f}%)\n"
            
            embed.add_field(
                name="📋 Series Breakdown",
                value=series_text,
                inline=False
            )
            
            # Cache status
            if self._cache_timestamp:
                cache_age = datetime.now() - self._cache_timestamp
                embed.add_field(
                    name="🔄 Cache Status",
                    value=f"Last updated: {cache_age.total_seconds():.0f}s ago",
                    inline=True
                )

            await ctx.send(embed=embed)

    @commands.command(name="enumberrecent", aliases=["erecent"])
    async def enumberrecent(self, ctx):
        """Show the most recently searched E-numbers this session."""
        if not self.recent_searches:
            embed = discord.Embed(
                title="📝 Recent Searches",
                description="No recent E-number searches this session.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="📝 Recently Searched E-numbers",
            description="E-numbers searched in this session:",
            color=discord.Color.blue()
        )
        
        # Group recent searches
        for i, code in enumerate(self.recent_searches, 1):
            embed.add_field(
                name=f"{i}. {code}",
                value="Click to search again",
                inline=True
            )

        await ctx.send(embed=embed)

    @commands.command(name="enumberinfo", aliases=["eninfo"])
    async def enumberinfo(self, ctx):
        """Show information about E-numbers and this bot."""
        embed = discord.Embed(
            title="🔬 E-numbers Bot Information",
            description="A comprehensive bot for looking up food additive E-numbers.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📚 What are E-numbers?",
            value="E-numbers are codes for substances that are permitted to be used as food additives in the European Union and other countries.",
            inline=False
        )
        
        embed.add_field(
            name="🔍 Available Commands",
            value=(
                "• `!enumber <code>` - Look up specific E-number\n"
                "• `!enumbersearch <query>` - Search by name or partial code\n"
                "• `!enumberlist [page]` - Browse all E-numbers\n"
                "• `!enumbercount` - Database statistics\n"
                "• `!enumberrecent` - Recent searches\n"
                "• `!enumberinfo` - This help message"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎨 Color Coding",
            value=(
                "• 🟢 Green: Natural colors (E100-E199)\n"
                "• 🔵 Blue: Preservatives (E200-E299)\n"
                "• 🟡 Yellow: Antioxidants (E300-E399)\n"
                "• 🟠 Orange: Thickeners (E400-E499)\n"
                "• 🔴 Red: Acidity regulators (E500-E599)\n"
                "• 🟣 Purple: Flavor enhancers (E600-E699)\n"
                "• ⚫ Grey: Others (E700+)"
            ),
            inline=False
        )
        
        embed.set_footer(text="Data provided by enumbers.jarvisdiscordbot.net")
        
        await ctx.send(embed=embed)


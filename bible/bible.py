import asyncio
import random
import re
from typing import Optional, Dict, Any, List

import aiohttp
import discord
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

class Bible(commands.Cog):
    """A comprehensive Bible cog using API.Bible service."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        # Global settings
        default_global = {
            "api_key": None,
            "default_bible_id": "61fd76eafa1577c2-03",  # NIV
            "max_verses_per_page": 10,
            "show_references": True,
            "show_footnotes": True
        }
        
        # Guild settings
        default_guild = {
            "enabled": True,
            "channel_restrictions": [],
            "role_restrictions": []
        }
        
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        
        # Common Bible books mapping
        self.book_mapping = {
            # Old Testament
            "genesis": "GEN", "gen": "GEN", "ge": "GEN",
            "exodus": "EXO", "exo": "EXO", "ex": "EXO",
            "leviticus": "LEV", "lev": "LEV", "le": "LEV",
            "numbers": "NUM", "num": "NUM", "nu": "NUM",
            "deuteronomy": "DEU", "deu": "DEU", "dt": "DEU",
            "joshua": "JOS", "jos": "JOS", "josh": "JOS",
            "judges": "JDG", "jdg": "JDG", "judg": "JDG",
            "ruth": "RUT", "rut": "RUT", "ru": "RUT",
            "1 samuel": "1SA", "1sam": "1SA", "1sa": "1SA", "1samuel": "1SA",
            "2 samuel": "2SA", "2sam": "2SA", "2sa": "2SA", "2samuel": "2SA",
            "1 kings": "1KI", "1kings": "1KI", "1ki": "1KI", "1k": "1KI",
            "2 kings": "2KI", "2kings": "2KI", "2ki": "2KI", "2k": "2KI",
            "1 chronicles": "1CH", "1chronicles": "1CH", "1ch": "1CH", "1chr": "1CH",
            "2 chronicles": "2CH", "2chronicles": "2CH", "2ch": "2CH", "2chr": "2CH",
            "ezra": "EZR", "ezr": "EZR", "ez": "EZR",
            "nehemiah": "NEH", "neh": "NEH", "ne": "NEH",
            "esther": "EST", "est": "EST", "es": "EST",
            "job": "JOB", "jb": "JOB",
            "psalms": "PSA", "psalm": "PSA", "ps": "PSA", "psa": "PSA",
            "proverbs": "PRO", "prov": "PRO", "pr": "PRO", "prv": "PRO",
            "ecclesiastes": "ECC", "ecc": "ECC", "ec": "ECC", "eccl": "ECC",
            "song of solomon": "SNG", "songs": "SNG", "sos": "SNG", "song": "SNG",
            "isaiah": "ISA", "isa": "ISA", "is": "ISA",
            "jeremiah": "JER", "jer": "JER", "je": "JER",
            "lamentations": "LAM", "lam": "LAM", "la": "LAM",
            "ezekiel": "EZK", "ezk": "EZK", "ezek": "EZK",
            "daniel": "DAN", "dan": "DAN", "da": "DAN",
            "hosea": "HOS", "hos": "HOS", "ho": "HOS",
            "joel": "JOL", "jol": "JOL", "jl": "JOL",
            "amos": "AMO", "amo": "AMO", "am": "AMO",
            "obadiah": "OBA", "oba": "OBA", "ob": "OBA",
            "jonah": "JON", "jon": "JON", "jnh": "JON",
            "micah": "MIC", "mic": "MIC", "mi": "MIC",
            "nahum": "NAH", "nah": "NAH", "na": "NAH",
            "habakkuk": "HAB", "hab": "HAB", "hb": "HAB",
            "zephaniah": "ZEP", "zep": "ZEP", "zeph": "ZEP",
            "haggai": "HAG", "hag": "HAG", "hg": "HAG",
            "zechariah": "ZEC", "zec": "ZEC", "zch": "ZEC",
            "malachi": "MAL", "mal": "MAL", "ml": "MAL",
            
            # New Testament
            "matthew": "MAT", "matt": "MAT", "mt": "MAT",
            "mark": "MRK", "mrk": "MRK", "mk": "MRK",
            "luke": "LUK", "luk": "LUK", "lk": "LUK",
            "john": "JHN", "jhn": "JHN", "jn": "JHN",
            "acts": "ACT", "act": "ACT", "ac": "ACT",
            "romans": "ROM", "rom": "ROM", "ro": "ROM",
            "1 corinthians": "1CO", "1corinthians": "1CO", "1cor": "1CO", "1co": "1CO",
            "2 corinthians": "2CO", "2corinthians": "2CO", "2cor": "2CO", "2co": "2CO",
            "galatians": "GAL", "gal": "GAL", "ga": "GAL",
            "ephesians": "EPH", "eph": "EPH", "ep": "EPH",
            "philippians": "PHP", "php": "PHP", "phil": "PHP",
            "colossians": "COL", "col": "COL", "co": "COL",
            "1 thessalonians": "1TH", "1thessalonians": "1TH", "1thess": "1TH", "1th": "1TH",
            "2 thessalonians": "2TH", "2thessalonians": "2TH", "2thess": "2TH", "2th": "2TH",
            "1 timothy": "1TI", "1timothy": "1TI", "1tim": "1TI", "1ti": "1TI",
            "2 timothy": "2TI", "2timothy": "2TI", "2tim": "2TI", "2ti": "2TI",
            "titus": "TIT", "tit": "TIT", "ti": "TIT",
            "philemon": "PHM", "phm": "PHM", "phlm": "PHM",
            "hebrews": "HEB", "heb": "HEB", "he": "HEB",
            "james": "JAS", "jas": "JAS", "ja": "JAS",
            "1 peter": "1PE", "1peter": "1PE", "1pet": "1PE", "1pe": "1PE",
            "2 peter": "2PE", "2peter": "2PE", "2pet": "2PE", "2pe": "2PE",
            "1 john": "1JN", "1john": "1JN", "1jn": "1JN",
            "2 john": "2JN", "2john": "2JN", "2jn": "2JN",
            "3 john": "3JN", "3john": "3JN", "3jn": "3JN",
            "jude": "JUD", "jud": "JUD", "ju": "JUD",
            "revelation": "REV", "rev": "REV", "re": "REV"
        }

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    def cog_unload(self):
        pass

    @commands.group(name="bible", aliases=["b"])
    async def bible_group(self, ctx):
        """Bible commands using API.Bible service."""
        pass

    @bible_group.command(name="setkey", aliases=["setapikey", "apikey"])
    @commands.is_owner()
    async def set_api_key(self, ctx, api_key: str):
        """Set the API.Bible API key."""
        await self.config.api_key.set(api_key)
        await ctx.send("✅ API key set successfully!")

    @bible_group.command(name="settings")
    @commands.is_owner()
    async def bible_settings(self, ctx):
        """View current Bible cog settings."""
        settings = await self.config.all()
        embed = discord.Embed(
            title="Bible Cog Settings",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="API Key", 
            value="✅ Set" if settings["api_key"] else "❌ Not Set", 
            inline=False
        )
        embed.add_field(
            name="Default Bible ID", 
            value=settings["default_bible_id"], 
            inline=False
        )
        embed.add_field(
            name="Max Verses Per Page", 
            value=settings["max_verses_per_page"], 
            inline=True
        )
        embed.add_field(
            name="Show References", 
            value="✅ Yes" if settings["show_references"] else "❌ No", 
            inline=True
        )
        embed.add_field(
            name="Show Footnotes", 
            value="✅ Yes" if settings["show_footnotes"] else "❌ No", 
            inline=True
        )
        await ctx.send(embed=embed)

    @bible_group.command(name="config")
    @commands.is_owner()
    async def config_bible(self, ctx, setting: str, value: str):
        """Configure Bible cog settings.
        
        Settings:
        - bible_id: Set default Bible ID
        - max_verses: Set max verses per page (1-20)
        - references: Toggle reference display (true/false)
        - footnotes: Toggle footnote display (true/false)
        """
        setting = setting.lower()
        
        if setting == "bible_id":
            await self.config.default_bible_id.set(value)
            await ctx.send(f"✅ Default Bible ID set to: {value}")
        elif setting == "max_verses":
            try:
                max_verses = int(value)
                if 1 <= max_verses <= 20:
                    await self.config.max_verses_per_page.set(max_verses)
                    await ctx.send(f"✅ Max verses per page set to: {max_verses}")
                else:
                    await ctx.send("❌ Max verses must be between 1 and 20.")
            except ValueError:
                await ctx.send("❌ Max verses must be a number.")
        elif setting == "references":
            if value.lower() in ["true", "yes", "1", "on"]:
                await self.config.show_references.set(True)
                await ctx.send("✅ Reference display enabled.")
            elif value.lower() in ["false", "no", "0", "off"]:
                await self.config.show_references.set(False)
                await ctx.send("✅ Reference display disabled.")
            else:
                await ctx.send("❌ Use true/false for references setting.")
        elif setting == "footnotes":
            if value.lower() in ["true", "yes", "1", "on"]:
                await self.config.show_footnotes.set(True)
                await ctx.send("✅ Footnote display enabled.")
            elif value.lower() in ["false", "no", "0", "off"]:
                await self.config.show_footnotes.set(False)
                await ctx.send("✅ Footnote display disabled.")
            else:
                await ctx.send("❌ Use true/false for footnotes setting.")
        else:
            await ctx.send("❌ Invalid setting. Use: bible_id, max_verses, references, or footnotes.")

    @bible_group.command(name="verse", aliases=["v"])
    async def get_verse(self, ctx, *, reference: str):
        """Get a specific Bible verse.
        
        Examples:
        - [p]bible verse John 3:16
        - [p]bible verse Genesis 1:1
        - [p]bible verse Psalm 23:1-6
        """
        await self._get_verse(ctx, reference)

    @bible_group.command(name="search", aliases=["s"])
    async def search_bible(self, ctx, *, query: str):
        """Search for Bible verses containing specific text.
        
        Example: [p]bible search love
        """
        await self._search_bible(ctx, query)

    @bible_group.command(name="random", aliases=["r"])
    async def random_verse(self, ctx):
        """Get a random Bible verse."""
        # Popular verses for random selection
        popular_verses = [
            "John 3:16", "Romans 8:28", "Jeremiah 29:11", "Philippians 4:13",
            "Proverbs 3:5-6", "Isaiah 40:31", "Matthew 28:19-20", "1 Corinthians 13:4-7",
            "Galatians 5:22-23", "Ephesians 2:8-9", "Psalm 23:1-6", "Matthew 6:33",
            "Romans 12:2", "2 Corinthians 5:17", "Hebrews 11:1", "James 1:2-4"
        ]
        
        random_reference = random.choice(popular_verses)
        await self._get_verse(ctx, random_reference)

    @bible_group.command(name="chapter", aliases=["c"])
    async def get_chapter(self, ctx, *, reference: str):
        """Get an entire Bible chapter.
        
        Examples:
        - [p]bible chapter John 3
        - [p]bible chapter Genesis 1
        - [p]bible chapter Psalm 23
        """
        await self._get_chapter(ctx, reference)

    @bible_group.command(name="info")
    async def bible_info(self, ctx):
        """Get information about available Bibles and the API."""
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("❌ API key not set. Owner must set it first.")
            return

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"api-key": api_key}
                
                # Get available Bibles
                async with session.get(
                    "https://api.scripture.api.bible/v1/bibles",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        bibles = data.get("data", [])
                        
                        embed = discord.Embed(
                            title="📖 API.Bible Information",
                            description="Available Bible translations and information",
                            color=discord.Color.green()
                        )
                        
                        # Show first 10 Bibles
                        bible_list = []
                        for bible in bibles[:10]:
                            name = bible.get("name", "Unknown")
                            language = bible.get("language", {}).get("name", "Unknown")
                            bible_list.append(f"**{name}** ({language})")
                        
                        embed.add_field(
                            name="Available Bibles (showing first 10)",
                            value="\n".join(bible_list) if bible_list else "No Bibles found",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="Total Bibles Available",
                            value=str(len(bibles)),
                            inline=True
                        )
                        
                        embed.add_field(
                            name="Current Default Bible",
                            value=await self.config.default_bible_id(),
                            inline=True
                        )
                        
                        embed.set_footer(text="Powered by API.Bible")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"❌ Error fetching Bible information: {response.status}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    async def _get_verse(self, ctx, reference: str):
        """Internal method to get a specific verse."""
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("❌ API key not set. Owner must set it first.")
            return

        # Parse reference
        parsed_ref = self._parse_reference(reference)
        if not parsed_ref:
            await ctx.send("❌ Invalid reference format. Use: Book Chapter:Verse or Book Chapter:Verse-Verse")
            return

        book, chapter, verse_start, verse_end = parsed_ref
        bible_id = await self.config.default_bible_id()

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"api-key": api_key}
                
                if verse_end and verse_end != verse_start:
                    # Range of verses
                    url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/passages/{book}.{chapter}.{verse_start}-{verse_end}"
                else:
                    # Single verse
                    url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/verses/{book}.{chapter}.{verse_start}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._send_verse_embed(ctx, data, f"{book} {chapter}:{verse_start}" + (f"-{verse_end}" if verse_end and verse_end != verse_start else ""))
                    elif response.status == 404:
                        await ctx.send("❌ Verse not found. Please check the reference.")
                    else:
                        await ctx.send(f"❌ Error fetching verse: {response.status}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    async def _get_chapter(self, ctx, reference: str):
        """Internal method to get an entire chapter."""
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("❌ API key not set. Owner must set it first.")
            return

        # Parse reference for chapter
        parts = reference.strip().split()
        if len(parts) < 2:
            await ctx.send("❌ Invalid format. Use: Book Chapter")
            return

        book_name = " ".join(parts[:-1]).lower()
        chapter = parts[-1]

        if not chapter.isdigit():
            await ctx.send("❌ Chapter must be a number.")
            return

        book = self.book_mapping.get(book_name)
        if not book:
            await ctx.send(f"❌ Book '{book_name}' not found. Use a valid book name.")
            return

        bible_id = await self.config.default_bible_id()

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"api-key": api_key}
                
                url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/passages/{book}.{chapter}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._send_chapter_embed(ctx, data, f"{book} {chapter}")
                    elif response.status == 404:
                        await ctx.send("❌ Chapter not found. Please check the reference.")
                    else:
                        await ctx.send(f"❌ Error fetching chapter: {response.status}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    async def _search_bible(self, ctx, query: str):
        """Internal method to search the Bible."""
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("❌ API key not set. Owner must set it first.")
            return

        bible_id = await self.config.default_bible_id()

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"api-key": api_key}
                
                url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/search"
                params = {
                    "query": query, 
                    "limit": 10,
                    "sort": "relevance"
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._send_search_results(ctx, data, query)
                    elif response.status == 401:
                        await ctx.send("❌ Unauthorized. Please check your API key.")
                    elif response.status == 403:
                        await ctx.send("❌ Not authorized to search this Bible. Your API key may not have search permissions.")
                    elif response.status == 404:
                        await ctx.send("❌ No results found for your search.")
                    else:
                        await ctx.send(f"❌ Error searching: {response.status}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    def _parse_reference(self, reference: str):
        """Parse a Bible reference string."""
        # Remove extra spaces and normalize
        reference = re.sub(r'\s+', ' ', reference.strip())
        
        # Pattern to match: Book Chapter:Verse or Book Chapter:Verse-Verse
        pattern = r'^(.+?)\s+(\d+):(\d+)(?:-(\d+))?$'
        match = re.match(pattern, reference)
        
        if not match:
            return None
        
        book_name = match.group(1).lower()
        chapter = match.group(2)
        verse_start = match.group(3)
        verse_end = match.group(4)
        
        # Map book name to abbreviation
        book = self.book_mapping.get(book_name)
        if not book:
            return None
        
        return book, chapter, verse_start, verse_end

    async def _send_verse_embed(self, ctx, data, reference):
        """Send a verse as an embed."""
        verse_data = data.get("data", {})
        content = verse_data.get("content", "")
        
        if not content:
            await ctx.send("❌ No content found for this verse.")
            return

        # Clean up the content
        content = self._clean_content(content)
        
        # Create embed
        embed = discord.Embed(
            title=f"📖 {reference}",
            description=content,
            color=discord.Color.gold()
        )
        
        # Add reference info
        if await self.config.show_references():
            reference_info = verse_data.get("reference", "")
            if reference_info:
                embed.add_field(name="Reference", value=reference_info, inline=False)
        
        # Add footnotes if available and enabled
        if await self.config.show_footnotes():
            footnotes = verse_data.get("footnotes", [])
            if footnotes:
                footnote_text = "\n".join([f"^{i+1} {note}" for i, note in enumerate(footnotes[:3])])
                if len(footnotes) > 3:
                    footnote_text += f"\n*...and {len(footnotes) - 3} more*"
                embed.add_field(name="Footnotes", value=footnote_text, inline=False)
        
        embed.set_footer(text="Powered by API.Bible")
        await ctx.send(embed=embed)

    async def _send_chapter_embed(self, ctx, data, reference):
        """Send a chapter as an embed."""
        chapter_data = data.get("data", {})
        content = chapter_data.get("content", "")
        
        if not content:
            await ctx.send("❌ No content found for this chapter.")
            return

        # Clean up the content
        content = self._clean_content(content)
        
        # Split content into pages if too long
        max_length = 2000
        if len(content) <= max_length:
            embed = discord.Embed(
                title=f"📖 {reference}",
                description=content,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Powered by API.Bible")
            await ctx.send(embed=embed)
        else:
            # Split into multiple embeds
            pages = list(pagify(content, delims=["\n\n", "\n"], page_length=max_length))
            embeds = []
            
            for i, page in enumerate(pages, 1):
                embed = discord.Embed(
                    title=f"📖 {reference} (Page {i}/{len(pages)})",
                    description=page,
                    color=discord.Color.blue()
                )
                embed.set_footer(text="Powered by API.Bible")
                embeds.append(embed)
            
            await menu(ctx, embeds, DEFAULT_CONTROLS)

    async def _send_search_results(self, ctx, data, query):
        """Send search results as embeds."""
        search_data = data.get("data", {})
        verses = search_data.get("verses", [])
        total = search_data.get("total", 0)
        
        if not verses:
            await ctx.send(f"❌ No results found for '{query}'.")
            return

        embeds = []
        for i, verse in enumerate(verses[:5], 1):  # Limit to 5 results
            content = verse.get("text", "")
            reference = verse.get("reference", "")
            
            if content and reference:
                # Clean content
                content = self._clean_content(content)
                
                # Truncate if too long
                if len(content) > 1000:
                    content = content[:1000] + "..."
                
                embed = discord.Embed(
                    title=f"🔍 Search Result {i}",
                    description=content,
                    color=discord.Color.green()
                )
                embed.add_field(name="Reference", value=reference, inline=False)
                
                # Add total results info
                if i == 1 and total > 0:
                    embed.add_field(
                        name="Total Results", 
                        value=f"{total} verses found", 
                        inline=False
                    )
                
                embed.set_footer(text=f"Search: '{query}' | Powered by API.Bible")
                embeds.append(embed)
        
        if embeds:
            await menu(ctx, embeds, DEFAULT_CONTROLS)
        else:
            await ctx.send(f"❌ No valid results found for '{query}'.")

    def _clean_content(self, content: str) -> str:
        """Clean up Bible content for display."""
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up verse numbers
        content = re.sub(r'<verse\s+[^>]*>(\d+)</verse>', r'\1', content)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content

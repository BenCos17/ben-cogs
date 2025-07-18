import discord
from redbot.core import commands, Config
import aiohttp
import difflib

class Enumbers(commands.Cog):
    """Look up E-numbers (food additives) using the enumbers API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        self.api_url = "https://enumbers.jarvisdiscordbot.net/api/enumbers"
        self.recent_searches = []  # Store recent searches for the session

    async def fetch_enumbers(self):
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; Discordbot/1.0; +https://discordapp.com)"}
            async with session.get(self.api_url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()

    @commands.command()
    async def enumber(self, ctx, *, code: str):
        """Look up an E-number (e.g. E621, E100, E950).
        You can type E-numbers with or without spaces, e.g. E120, e 120, or E  1 2 0.
        """
        code = code.upper().replace(" ", "")
        if not code.startswith("E"):
            code = "E" + code
        try:
            data = await self.fetch_enumbers()
            if data is None:
                await ctx.send(f"❌ Could not reach the E-numbers API.")
                returnbo
        except aiohttp.ClientError as e:
            await ctx.send(f"❌ HTTP error: {type(e).__name__}: {e}")
            return
        except Exception as e:
            await ctx.send(f"❌ Unexpected error: {type(e).__name__}: {e}")
            return
        found = None
        for item in data:
            if item.get("code", "").upper() == code:
                found = item
                break
        if not found:
            # Fuzzy match suggestions
            codes = [item.get("code", "") for item in data]
            names = [item.get("name", "") for item in data]
            close_codes = difflib.get_close_matches(code, codes, n=3, cutoff=0.6)
            close_names = difflib.get_close_matches(code, names, n=3, cutoff=0.6)
            suggestions = close_codes + [c for c in codes if code in c] + close_names
            suggestions = list(dict.fromkeys(suggestions))  # Remove duplicates, preserve order
            if suggestions:
                await ctx.send(f"❌ E-number `{code}` not found. Did you mean: {', '.join(suggestions[:3])}?")
            else:
                await ctx.send(f"❌ E-number `{code}` not found.")
            return
        # Add to recent searches
        self.recent_searches.insert(0, found.get("code", code))
        self.recent_searches = self.recent_searches[:10]
        name = found.get("name", "Unknown")
        url = found.get("openfoodfacts_url")
        additive = found.get("openfoodfacts_additive")
        embed = discord.Embed(
            title=f"{code}: {name}",
            description=f"**{name}**",
            color=discord.Color.green()
        )
        if url:
            embed.add_field(name="OpenFoodFacts", value=f"[OpenFoodFacts Link]({url})", inline=False)
        if additive:
            add_name = additive.get("name")
            add_url = additive.get("url")
            wikidata = additive.get("sameAs", [])
            if add_name:
                embed.add_field(name="Additive Name", value=add_name, inline=False)
            if add_url:
                embed.add_field(name="Additive Info", value=f"[More Info]({add_url})", inline=False)
            if wikidata:
                wikidata_links = "\n".join(f"[Wikidata]({link})" for link in wikidata)
                embed.add_field(name="Wikidata", value=wikidata_links, inline=False)
        # Plain text summary fallback
        summary = f"{code}: {name}\n"
        if url:
            summary += f"OpenFoodFacts: {url}\n"
        if additive:
            if add_name:
                summary += f"Additive Name: {add_name}\n"
            if add_url:
                summary += f"Additive Info: {add_url}\n"
            if wikidata:
                summary += f"Wikidata: {'; '.join(wikidata)}\n"
        try:
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(summary)

    @commands.command()
    async def enumbersearch(self, ctx, *, query: str):
        """Search for E-numbers by code or name (partial/fuzzy)."""
        try:
            data = await self.fetch_enumbers()
            if data is None:
                await ctx.send(f"❌ Could not reach the E-numbers API.")
                return
        except Exception as e:
            await ctx.send(f"❌ Error: {type(e).__name__}: {e}")
            return
        query = query.upper().replace(" ", "")
        matches = [item for item in data if query in item.get("code", "").upper() or query in item.get("name", "").upper()]
        if not matches:
            # Fuzzy match
            codes = [item.get("code", "") for item in data]
            names = [item.get("name", "") for item in data]
            close_codes = difflib.get_close_matches(query, codes, n=5, cutoff=0.5)
            close_names = difflib.get_close_matches(query, names, n=5, cutoff=0.5)
            suggestions = close_codes + close_names
            suggestions = list(dict.fromkeys(suggestions))
            if suggestions:
                await ctx.send(f"No direct matches found. Did you mean: {', '.join(suggestions[:5])}?")
            else:
                await ctx.send("No matches found.")
            return
        msg = "**Search results:**\n"
        for item in matches[:10]:
            msg += f"`{item.get('code', '?')}`: {item.get('name', '?')}\n"
        if len(matches) > 10:
            msg += f"...and {len(matches)-10} more. Refine your search for fewer results."
        await ctx.send(msg)

    @commands.command()
    async def enumberlist(self, ctx, page: int = 1):
        """List all E-numbers (paginated, 20 per page)."""
        try:
            data = await self.fetch_enumbers()
            if data is None:
                await ctx.send(f"❌ Could not reach the E-numbers API.")
                return
        except Exception as e:
            await ctx.send(f"❌ Error: {type(e).__name__}: {e}")
            return
        per_page = 20
        total = len(data)
        pages = (total + per_page - 1) // per_page
        if page < 1 or page > pages:
            await ctx.send(f"Page must be between 1 and {pages}.")
            return
        start = (page - 1) * per_page
        end = start + per_page
        msg = f"**E-numbers List (Page {page}/{pages}):**\n"
        for item in data[start:end]:
            msg += f"`{item.get('code', '?')}`: {item.get('name', '?')}\n"
        await ctx.send(msg)

    @commands.command()
    async def enumbercount(self, ctx):
        """Show the total number of E-numbers in the database."""
        try:
            data = await self.fetch_enumbers()
            if data is None:
                await ctx.send(f"❌ Could not reach the E-numbers API.")
                return
        except Exception as e:
            await ctx.send(f"❌ Error: {type(e).__name__}: {e}")
            return
        await ctx.send(f"There are {len(data)} E-numbers in the database.")

    @commands.command()
    async def enumberrecent(self, ctx):
        """Show the most recently searched E-numbers this session."""
        if not self.recent_searches:
            await ctx.send("No recent E-number searches this session.")
            return
        msg = "**Recently searched E-numbers:**\n" + ", ".join(self.recent_searches)
        await ctx.send(msg)


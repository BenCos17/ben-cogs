import discord
from redbot.core import commands, Config
import aiohttp

class Enumbers(commands.Cog):
    """Look up E-numbers (food additives) using the enumbers API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=3141592653)
        self.api_url = "https://enumbers.jarvisdiscordbot.net/api/enumbers"

    @commands.command()
    async def enumber(self, ctx, *, code: str):
        """Look up an E-number (e.g. E621, E100, E950).
        You can type E-numbers with or without spaces, e.g. E120, e 120, or E  1 2 0.
        """
        code = code.upper().replace(" ", "")
        if not code.startswith("E"):
            code = "E" + code
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0 (compatible; Discordbot/1.0; +https://discordapp.com)"}
                async with session.get(self.api_url, headers=headers) as resp:
                    if resp.status != 200:
                        await ctx.send(f"❌ Could not reach the E-numbers API. Status: {resp.status}")
                        return
                    data = await resp.json()
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
            await ctx.send(f"❌ E-number `{code}` not found.")
            return
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
        await ctx.send(embed=embed)


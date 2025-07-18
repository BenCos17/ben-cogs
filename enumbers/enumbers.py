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
    async def enumber(self, ctx, code: str):
        """Look up an E-number (e.g. E621, E100, E950)."""
        code = code.upper().replace(" ", "")
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url) as resp:
                if resp.status != 200:
                    await ctx.send("❌ Could not reach the E-numbers API.")
                    return
                data = await resp.json()
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
        embed = discord.Embed(title=f"{code}: {name}", color=discord.Color.green())
        if url:
            embed.add_field(name="OpenFoodFacts", value=f"[Link]({url})", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Enumbers(bot))

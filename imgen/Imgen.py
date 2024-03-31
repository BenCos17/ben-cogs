import discord
from redbot.core import commands, Config
import aiohttp

class Imgen(commands.Cog):
    """Cog for interacting with the Imgen API"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976, force_registration=True)
        default_global = {}
        self.config.register_global(**default_global)

    @commands.command()
    async def memes(self, ctx, top_text: str, bottom_text: str, color: str = None, font: str = None):
        """Generate a meme with top and bottom text"""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://imgen.red/api/meme_v2', params={'top_text': top_text, 'bottom_text': bottom_text, 'color': color, 'font': font}) as response:
                if response.status == 200:
                    meme_url = await response.text()
                    await ctx.send(meme_url)
                else:
                    await ctx.send("Error generating meme")


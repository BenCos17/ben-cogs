import discord
from redbot.core import commands
from googletrans import Translator

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    @commands.command()
    async def translate(self, ctx, lang, *, message):
        try:
            translated = self.translator.translate(message, dest=lang)
            await ctx.send(f"{translated.text}")
        except Exception as e:
            await ctx.send(f"Error translating message: {e}")

def setup(bot):
    bot.add_cog(Translate(bot))

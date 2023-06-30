from .roast import Roast

def setup(bot):
    cog = Roast(bot)
    bot.add_cog(cog)

from .roast import RoastCog

def setup(bot):
    cog = RoastCog(bot)
    bot.add_cog(cog)

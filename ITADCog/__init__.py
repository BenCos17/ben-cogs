from .itad_cog import ITADCog 

def setup(bot):
    cog = ITADCog(bot)
    bot.add_cog(cog)

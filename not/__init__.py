from .not import Not

async def setup(bot):
    cog = Not(bot)
    bot.add_cog(cog)

from .amazon import Amazon

async def setup(bot):
    cog = Amazon(bot)
    await bot.add_cog(cog)

from redbot.core.bot import Red

from .amazon import Amazon

async def setup(bot: Red):
    cog = Amazon(bot)
    await bot.add_cog(cog)

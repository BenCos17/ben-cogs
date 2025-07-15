from redbot.core.bot import Red

from .amazon import Amazon

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot: Red):
    cog = Amazon(bot)
    await bot.add_cog(cog)

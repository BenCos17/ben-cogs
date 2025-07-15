

from redbot.core.bot import Red

from .calendar import Calendar

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot: Red):
    await bot.add_cog(Calendar(bot))

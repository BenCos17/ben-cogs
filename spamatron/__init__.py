from redbot.core.bot import Red

from .spamatron import Spamatron

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot: Red):
    await bot.add_cog(Spamatron(bot))
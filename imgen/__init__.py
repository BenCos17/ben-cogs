from redbot.core.bot import Red

from .Imgen import Imgen

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot: Red):
    await bot.add_cog(Imgen(bot))
from redbot.core.bot import Red

from .servertools import Servertools

async def setup(bot: Red):
    await bot.add_cog(Servertools(bot))
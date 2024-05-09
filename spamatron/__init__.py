from redbot.core.bot import Red

from .spamatron import Spamatron

async def setup(bot: Red):
    await bot.add_cog(Spamatron(bot))
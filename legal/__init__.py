from redbot.core.bot import Red

from .legal import Legal

async def setup(bot: Red):
    await bot.add_cog(Legal(bot))

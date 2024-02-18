
from redbot.core.bot import Red

from .not import Not

async def setup(bot: Red):
    await bot.add_cog(Not(bot))
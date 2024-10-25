from redbot.core.bot import Red
from .bell import BellCog
async def setup(bot: Red):
    await bot.add_cog(BellCog(bot))
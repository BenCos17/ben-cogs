from redbot.core.bot import Red
from .bell import Bell
async def setup(bot: Red):
    await bot.add_cog(Bell(bot))
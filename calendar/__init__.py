

from redbot.core.bot import Red

from .calendar import Calendar

async def setup(bot: Red):
    await bot.add_cog(Calendar(bot))

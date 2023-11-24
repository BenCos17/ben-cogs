from redbot.core.bot import Red

from .court import Court

async def setup(bot: Red):
    await bot.add_cog(Court(bot))
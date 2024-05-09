from redbot.core.bot import Red

from .application import Application

async def setup(bot: Red):
    await bot.add_cog(Application(bot))
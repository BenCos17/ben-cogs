from redbot.core.bot import Red

from .scp import ScpLookup

async def setup(bot: Red):
    await bot.add_cog(ScpLookup(bot))
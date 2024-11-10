from redbot.core.bot import Red

from .scp import SCPLookup

async def setup(bot: Red):
    await bot.add_cog(ScpLookup(bot))
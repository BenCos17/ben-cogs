from redbot.core.bot import Red

from .scp import scpLookup

async def setup(bot: Red):
    await bot.add_cog(scpLookup(bot))
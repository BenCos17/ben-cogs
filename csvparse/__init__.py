

from redbot.core.bot import Red

from .csvparse import CSVParse

async def setup(bot: Red):
    await bot.add_cog(CSVParse(bot))

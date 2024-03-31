from redbot.core.bot import Red

from .Imgen import Imgen

async def setup(bot: Red):
    await bot.add_cog(Imgen(bot))
from redbot.core.bot import Red

from .Imgenmgen import Imgen

async def setup(bot: Red):
    await bot.add_cog(Imgen(bot))
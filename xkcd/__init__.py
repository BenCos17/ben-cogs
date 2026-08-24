
from .xkcd import XKCD
async def setup(bot):
    await bot.add_cog(XKCD(bot))

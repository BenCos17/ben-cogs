
from .xkcd import XKCD
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(XKCD(bot))

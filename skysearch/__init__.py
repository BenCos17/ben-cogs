"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

from .skysearch import Skysearch

async def setup(bot):
    """Add the Skysearch cog to the bot."""
    await bot.add_cog(Skysearch(bot))
"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

from .skysearch import Skysearch

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot):
    """Add the Skysearch cog to the bot."""
    cog = Skysearch(bot)
    await bot.add_cog(cog)
    # Dashboard integration is now handled within the main cog.
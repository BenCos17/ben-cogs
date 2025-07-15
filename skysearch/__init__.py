"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

from .skysearch import Skysearch

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot):
    """Add the Skysearch cog to the bot."""
    await bot.add_cog(Skysearch(bot))
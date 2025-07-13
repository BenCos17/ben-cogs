"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

from .skysearch import Skysearch

def setup(bot):
    """Add the Skysearch cog to the bot."""
    bot.add_cog(Skysearch(bot))
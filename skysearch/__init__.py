"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

from redbot.core.i18n import Translator

_ = Translator("Skysearch", __file__)

from .skysearch import Skysearch

__red_end_user_data_statement__ = "This cog stores data when a user adds an aircraft to their watchlist and uses the user id to know what user added it."

async def setup(bot):
    cog = Skysearch(bot)
    await bot.add_cog(cog)
    # Dashboard integration is handled within the dashboard_integration.py file
"""
SkySearch - A powerful aircraft tracking and information Discord bot cog
"""

from .skysearch import Skysearch
from .commands.dashboard_integration import DashboardIntegration

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot):
    """Add the Skysearch cog to the bot."""
    cog = Skysearch(bot)
    await bot.add_cog(cog)
    # Register dashboard integration if Dashboard cog is loaded
    dashboard_cog = bot.get_cog("Dashboard")
    if dashboard_cog:
        dashboard_integration = DashboardIntegration()
        await bot.add_cog(dashboard_integration)
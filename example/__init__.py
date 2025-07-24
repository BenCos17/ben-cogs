"""
SquawkExample - Example cog demonstrating how to use the SquawkAlertAPI
"""

from .squawk_cog import SquawkCog

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot):
    """Add the SquawkExample cog to the bot."""
    from .squawk_cog import setup as squawk_setup
    await squawk_setup(bot) 
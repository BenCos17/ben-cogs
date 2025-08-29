"""
JarvisBan Cog for RedBot

A cog that allows users to ban someone by saying "jarvis ban this guy"
"""

from .jarvisban import JarvisBan

__red_end_user_data_statement__ = "This cog does not persistently store data about users."

def setup(bot):
    """Add the cog to the bot"""
    bot.add_cog(JarvisBan(bot))

"""Voice cog package for ben-cogs

Exports a setup function for Red and package metadata.
"""

from .voice import VoiceRecvCog

__red_end_user_data_statement__ = "This cog does not persist end user data." 


async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(VoiceRecvCog(bot))

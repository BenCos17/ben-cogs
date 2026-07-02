"""Lightning - A Redbot cog for tracking lightning strikes."""

from .lightning import Lightning


async def setup(bot):
    """Load the Lightning cog into the bot."""
    await bot.add_cog(Lightning(bot))

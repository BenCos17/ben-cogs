"""Counter cog package for ben-cogs

Adds a simple, flexible counter system that supports per-guild, per-user, and global counters.
"""

from .counter import Counter

__red_end_user_data_statement__ = (
    "This cog stores counters and their numeric values. It stores guild IDs, user IDs (for user-scoped counters), "
    "counter names, and numeric values. It does not store message content or other personal data."
)

async def setup(bot):
    await bot.add_cog(Counter(bot))

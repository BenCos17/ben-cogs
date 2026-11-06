from redbot.core.bot import Red

from .report import BotReport

__red_end_user_data_statement__ = (
    "This cog processes and forwards Discord user IDs, usernames, message content, attachment URLs, "
    "and report reasons to the bot owner's configured report channel. It does not persist this data on the bot but does store it in the report channel on discord."
)


async def setup(bot: Red):
    await bot.add_cog(BotReport(bot))
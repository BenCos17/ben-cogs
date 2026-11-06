from .usagestats import UsageStats

__red_end_user_data_statement__ = (
    "This cog logs which commands are used: the time, the Discord user ID, the server ID and the command name. "
    "It is only used for usage counts, kept for about 400 days, and deleted on a data deletion request."
)


async def setup(bot):
  await bot.add_cog(UsageStats(bot))

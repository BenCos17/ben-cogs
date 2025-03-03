from .watchdog import Watchdog

__red_end_user_data_statement__ = "This cog monitors the bot's status and interacts with systemd's watchdog."

def setup(bot):
    bot.add_cog(Watchdog(bot))

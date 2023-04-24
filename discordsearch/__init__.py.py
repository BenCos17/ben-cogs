from .discordsearch  import DiscordSearch


def setup(bot):
    bot.add_cog(DiscordSearch(bot))

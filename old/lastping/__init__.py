from .lastping import LastPingCog


def setup(bot):
    bot.add_cog(LastPingCog(bot))

from .channelcountdown import ChannelCountdown

def setup(bot):
    bot.add_cog(ChannelCountdown(bot))

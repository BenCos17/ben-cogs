from .botinfoembed import BotInfoEmbed

def setup(bot):
    cog = BotInfoEmbed(bot)
    bot.add_cog(cog)

from .botinfoembed import BotInfoEmbed

async def setup(bot):
    cog = BotInfoEmbed(bot)
    bot.add_cog(cog)

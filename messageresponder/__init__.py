from .messageresponder import MessageResponder

async def setup(bot):
    cog = MessageResponder(bot)
    bot.add_cog(cog)
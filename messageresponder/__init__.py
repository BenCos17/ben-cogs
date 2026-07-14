from .messageresponder import MessageResponder

async def setup(bot):
    await bot.add_cog(MessageResponder(bot))
from .ampremover import AmputatorBot

async def setup(bot):
    await bot.add_cog(AmputatorBot(bot))


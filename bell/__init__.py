from .bell import BellCog

async def setup(bot):
    bot.add_cog(BellCog(bot))

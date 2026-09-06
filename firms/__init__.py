from .firms import Firms

async def setup(bot):
    await bot.add_cog(Firms(bot))
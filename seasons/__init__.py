from .seasons import Seasons

async def setup(bot):
    await bot.add_cog(Seasons(bot))

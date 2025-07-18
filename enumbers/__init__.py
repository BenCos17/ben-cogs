from .enumbers import Enumbers

async def setup(bot):
    await bot.add_cog(Enumbers(bot))

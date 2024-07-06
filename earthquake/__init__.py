from .earthquake import Earthquake

async def setup(bot):
    await bot.add_cog(Earthquake(bot))

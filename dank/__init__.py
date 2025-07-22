from .dank import Dank

async def setup(bot):
    await bot.add_cog(Dank())

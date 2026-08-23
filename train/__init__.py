from .train import Train


async def setup(bot):
  await bot.add_cog(Train(bot))
from .imagemanipulation import ImageManipulation


async def setup(bot):
    await bot.add_cog(ImageManipulation(bot))

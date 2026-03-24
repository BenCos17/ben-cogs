from .image import ImageTools


async def setup(bot):
    await bot.add_cog(ImageTools(bot))

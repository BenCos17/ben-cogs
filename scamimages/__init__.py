from .scamimages import ScamImages


async def setup(bot):
    await bot.add_cog(ScamImages(bot))

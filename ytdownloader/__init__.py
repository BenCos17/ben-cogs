from .converter import YTDownloader

async def setup(bot):
    await bot.add_cog(YTDownloader(bot))
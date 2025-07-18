from .facebook_video_downloader import FacebookVideoDownloader

async def setup(bot):
    await bot.add_cog(FacebookVideoDownloader(bot)) 
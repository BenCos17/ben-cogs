from .facebook_video_downloader import FacebookVideoDownloader

def setup(bot):
    bot.add_cog(FacebookVideoDownloader(bot)) 
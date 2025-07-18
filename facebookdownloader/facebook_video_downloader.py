import discord
from redbot.core import commands
import yt_dlp
import os

class FacebookVideoDownloader(commands.Cog):
    """Download Facebook videos via a command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fbvideo(self, ctx, url: str):
        """Download a Facebook video from a public URL and upload it here."""
        async with ctx.typing():
            filename = "fb_video.mp4"
            ydl_opts = {
                'outtmpl': filename,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'noplaylist': True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                if not os.path.exists(filename):
                    await ctx.send("Could not download the video. Please check the URL or try again later.")
                    return
                await ctx.send(file=discord.File(filename))
                os.remove(filename)
            except Exception as e:
                await ctx.send(f"Error: {e}") 
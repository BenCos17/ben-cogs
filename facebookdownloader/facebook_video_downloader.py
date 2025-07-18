import discord
from redbot.core import commands
import yt_dlp
import os
import tempfile

class FacebookVideoDownloader(commands.Cog):
    """Download Facebook videos via a command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fbvideo(self, ctx, url: str):
        """
        Download a Facebook video from a public URL and upload it here.

        **Usage:**
        `[p]fbvideo <facebook_video_url>`
        Example: `[p]fbvideo https://www.facebook.com/watch/?v=1234567890`
        """
        # (6) Check for permissions to send files
        if not ctx.channel.permissions_for(ctx.me).send_messages or not ctx.channel.permissions_for(ctx.me).attach_files:
            await ctx.send("I don't have permission to send files in this channel.")
            return
        async with ctx.typing():
            # (5) User feedback: status message
            status_msg = await ctx.send("Starting download... This may take a moment.")
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'noplaylist': True,
            }
            try:
                # (4) Use tempfile for safe file handling
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmpfile:
                    ydl_opts['outtmpl'] = tmpfile.name
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    await status_msg.edit(content="Uploading video to Discord...")
                    if not os.path.exists(tmpfile.name):
                        await ctx.send("Could not download the video. Please check the URL or try again later.")
                        return
                    await ctx.send(file=discord.File(tmpfile.name))
                    os.remove(tmpfile.name)
                await status_msg.delete()
            except Exception as e:
                await status_msg.edit(content=f"Error: {e}") 
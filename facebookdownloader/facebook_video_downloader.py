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
            # Cookie support: look for a cookies file
            cookies_path = None
            for candidate in ["facebook_cookies.txt", "instagram_cookies.txt", "cookies.txt"]:
                if os.path.exists(candidate):
                    cookies_path = candidate
                    break
            if cookies_path:
                ydl_opts['cookiefile'] = cookies_path
            try:
                # (4) Use tempfile for safe file handling
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmpfile:
                    ydl_opts['outtmpl'] = tmpfile.name
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    await status_msg.edit(content="Checking file size...")
                    if not os.path.exists(tmpfile.name):
                        await status_msg.edit(content="Could not download the video. Please check the URL or try again later.")
                        return
                    file_size = os.path.getsize(tmpfile.name)
                    max_size = 8 * 1024 * 1024  # 8MB default Discord limit
                    file_size_mb = file_size / (1024 * 1024)
                    if file_size == 0:
                        await status_msg.edit(content="The downloaded file is empty. This usually means the video is private, requires login, or yt-dlp was blocked. The bot owner can provide cookies for authentication. See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp")
                        os.remove(tmpfile.name)
                        return
                    if file_size > max_size:
                        await status_msg.edit(content=f"The downloaded video is too large to upload to Discord.\nFile size: {file_size_mb:.2f} MB (limit: {max_size // (1024 * 1024)} MB).\nUpload failed because the file exceeds Discord's upload limit.")
                        os.remove(tmpfile.name)
                        return
                    await status_msg.edit(content="Uploading video to Discord...")
                    await ctx.send(file=discord.File(tmpfile.name))
                    os.remove(tmpfile.name)
                await status_msg.delete()
            except Exception as e:
                err_str = str(e).lower()
                if 'login required' in err_str or 'cookies' in err_str or 'private' in err_str or 'not available' in err_str:
                    await status_msg.edit(content="Download failed: Login or cookies required. The bot owner can provide cookies for authentication. See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp")
                else:
                    await status_msg.edit(content=f"Error: {e}") 
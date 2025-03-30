import discord
from redbot.core import commands, Config
from yt_dlp import YoutubeDL
import asyncio
from redbot.core import data_manager
from pathlib import Path
import subprocess
import os
import validators

class YTDownloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_folder = data_manager.cog_data_path(cog_instance=self)
        self.config = Config.get_conf(self, identifier=123456789)
        self.config.register_global(use_cookies=False, cookie_method="browser", cookie_path="")

    async def download_and_convert(self, ctx, url, to_mp3=False):
        if not validators.url(url):
            await ctx.send("`Invalid URL provided. Please provide a valid YouTube video URL.`")
            return

        try:
            output_folder = self.data_folder / ("mp3" if to_mp3 else "mp4")
            use_cookies = await self.config.use_cookies()
            cookie_method = await self.config.cookie_method()
            cookie_path = await self.config.cookie_path()

            ydl_opts = {
                'format': 'bestaudio/best' if to_mp3 else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': str(output_folder / f"%(id)s.{'mp3' if to_mp3 else 'mp4'}"),
                'default_search': 'auto',
                'progress_hooks': [self.my_hook],
            }

            if use_cookies:
                if cookie_method == "browser":
                    ydl_opts['cookies_from_browser'] = ('chrome',)  # Change if needed
                elif cookie_method == "file" and cookie_path:
                    ydl_opts['cookiefile'] = cookie_path

            conversion_message = await ctx.send(f"`Downloading video...`")

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            await asyncio.sleep(5)
            user = ctx.message.author
            video_id = ydl.extract_info(url, download=False)['id']
            downloaded_file_path = output_folder / f"{video_id}.{'mp3' if to_mp3 else 'mp4'}"

            if downloaded_file_path.exists():
                converted_extension = 'mp3' if to_mp3 else 'mp4'
                converted_file_path = output_folder / f"{video_id}_converted.{converted_extension}"
                subprocess.run(['ffmpeg', '-i', str(downloaded_file_path), '-c:v', 'libx264', str(converted_file_path)])

                try:
                    await conversion_message.edit(content=f"`Uploading {'audio' if to_mp3 else 'video'}...`")
                    await ctx.send(f'{user.mention}, `Here is the converted {"audio" if to_mp3 else "video"}:`',
                                    file=discord.File(str(converted_file_path)))

                    downloaded_file_path.unlink()
                    converted_file_path.unlink()
                except discord.errors.HTTPException as upload_error:
                    await ctx.send(f"`An error occurred during upload. Error details: {upload_error}`")
                    downloaded_file_path.unlink()
                    converted_file_path.unlink()
            else:
                await ctx.send("`An error occurred during conversion. The downloaded file does not exist.`")
        except Exception as e:
            await ctx.send(f"`An error occurred. Please check the URL and try again.\nError details: {str(e)}`")

    def my_hook(self, d):
        if d['status'] == 'finished':
            print('Done downloading, now converting...')

    @commands.command()
    async def ytmp3(self, ctx, *, query):
        """Converts a YouTube video to MP3."""
        await self.download_and_convert(ctx, query, to_mp3=True)

    @commands.command()
    async def ytmp4(self, ctx, *, query):
        """Converts a YouTube video to MP4."""
        await self.download_and_convert(ctx, query, to_mp3=False)

    @commands.command()
    async def ytsetcookies(self, ctx, enable: bool, method: str = "browser", path: str = ""):
        """Enable or disable cookies and set the method.

        - `enable`: `True` to use cookies, `False` to disable.
        - `method`: `browser` (default) or `file`.
        - `path`: Path to cookies.txt (if method is 'file').
        """
        if method not in ["browser", "file"]:
            await ctx.send("`Invalid method. Use 'browser' or 'file'.`")
            return

        await self.config.use_cookies.set(enable)
        await self.config.cookie_method.set(method)
        await self.config.cookie_path.set(path if method == "file" else "")

        await ctx.send(f"`Cookies {'enabled' if enable else 'disabled'}. Method: {method}{' (Path: ' + path + ')' if method == 'file' else ''}`")

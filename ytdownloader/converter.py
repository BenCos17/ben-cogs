import discord
from redbot.core import commands, data_manager
from yt_dlp import YoutubeDL
import asyncio
from pathlib import Path
import subprocess
import os
import validators  # New import for URL validation
import json

class YTDownloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Use Redbot's data directory directly
        self.data_folder = data_manager.cog_data_path(cog_instance=self)
        self.cookie_preference_file = self.data_folder / "cookies.json"  # Change to cookies.json for clarity
        self.cookie_preference = self.load_cookie_preference()

    def load_cookie_preference(self):
        if self.cookie_preference_file.exists():
            with open(self.cookie_preference_file, 'r') as f:
                return json.load(f).get("use_cookies", False)
        return False

    def save_cookie_preference(self, use_cookies):
        with open(self.cookie_preference_file, 'w') as f:
            json.dump({"use_cookies": use_cookies}, f)

    async def download_and_convert(self, ctx, url, to_mp3=False):
        # Check if the provided URL is valid
        if not validators.url(url):
            await ctx.send("`Invalid URL provided. Please provide a valid YouTube video URL.`")
            return

        try:
            output_folder = self.data_folder / ("mp3" if to_mp3 else "mp4")

            ydl_opts = {
                'format': 'bestaudio/best' if to_mp3 else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': str(output_folder / f"%(id)s.{'mp3' if to_mp3 else 'mp4'}"),
                'default_search': 'auto',  # Set default search
                'progress_hooks': [self.my_hook],  # Add progress hook
            }

            # Always add cookies option
            ydl_opts['cookies'] = str(self.data_folder / "cookies.txt")  # Specify the path to your cookies file

            conversion_message = await ctx.send(f"`Converting video...`")

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Wait for the download and conversion to complete
            await asyncio.sleep(5)

            user = ctx.message.author
            video_id = ydl.extract_info(url)['id']
            downloaded_file_path = output_folder / f"{video_id}.{'mp3' if to_mp3 else 'mp4'}"
            renamed_file_path = output_folder / f"{video_id}.{'mp3' if to_mp3 else 'mp4'}"

            # Check if the downloaded file exists before renaming
            if downloaded_file_path.exists():
                # Convert the video to MP4 with h264 codec using ffmpeg
                converted_extension = 'mp3' if to_mp3 else 'mp4'
                converted_file_path = output_folder / f"{video_id}_converted.{converted_extension}"
                subprocess.run(['ffmpeg', '-i', str(downloaded_file_path), '-c:v', 'libx264', str(converted_file_path)])

                # Try uploading the file
                try:
                    await conversion_message.edit(content=f"`Uploading {'audio' if to_mp3 else 'video'}...`")
                    # Send a new message with the converted file, mentioning the user
                    await ctx.send(f'{user.mention}, `Here is the converted {"audio" if to_mp3 else "video"}:`',
                                    file=discord.File(str(converted_file_path)))
                    
                    # Remove the downloaded and converted files
                    downloaded_file_path.unlink()
                    converted_file_path.unlink()

                except discord.errors.HTTPException as upload_error:
                    # If uploading fails, send an error message
                    await ctx.send(f"`An error occurred during upload. Please check the file and try again.\nError details: {upload_error}`")
                    # Remove the downloaded and converted files
                    downloaded_file_path.unlink()
                    converted_file_path.unlink()
            else:
                await ctx.send("`An error occurred during conversion. The downloaded file does not exist.`")
                # Remove the downloaded and converted files
                downloaded_file_path.unlink()
                converted_file_path.unlink()

        except Exception as e:
            error_message = str(e)
            await ctx.send(f"`An error occurred during conversion. Please check the URL and try again.\nError details: {error_message}`")

    def my_hook(self, d):
        if d['status'] == 'finished':
            print('Done downloading, now converting...')

    @commands.command()
    async def ytmp3(self, ctx, *, query):
        """
        Converts a YouTube video to MP3.

        Parameters:
        `<query>` The search query or URL of the video you want to convert.
        """
        await self.download_and_convert(ctx, query, to_mp3=True)

    @commands.command()
    async def ytmp4(self, ctx, *, query):
        """
        Converts a YouTube video to MP4.

        Parameters:
        `<query>` The search query or URL of the video you want to convert.
        """
        await self.download_and_convert(ctx, query, to_mp3=False)

    @commands.command()
    async def toggle_cookies(self, ctx):
        """
        Toggles the use of cookies for downloading videos and saves the preference.
        """
        self.cookie_preference = not self.cookie_preference
        self.save_cookie_preference(self.cookie_preference)
        status = "enabled" if self.cookie_preference else "disabled"
        await ctx.send(f"`Cookie usage has been {status}.`")

    @commands.command()
    async def check_cookies(self, ctx):
        """
        Checks if the cookies file exists in the data directory.
        """
        cookies_file_path = str(self.data_folder / "cookies.txt")  # Adjust if you use a different name
        if os.path.exists(cookies_file_path):
            await ctx.send(f"`Cookies file found at: {cookies_file_path}`")
        else:
            await ctx.send("`Cookies file not found. Please ensure it is in the correct directory.`")

    @commands.command()
    async def debug_ydl_opts(self, ctx, url, to_mp3: bool = False):
        """
        Debugs the ydl_opts variables being passed to yt-dlp.
        """
        output_folder = self.data_folder / ("mp3" if to_mp3 else "mp4")

        ydl_opts = {
            'format': 'bestaudio/best' if to_mp3 else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(output_folder / f"%(id)s.{'mp3' if to_mp3 else 'mp4'}"),
            'default_search': 'auto',  # Set default search
            'progress_hooks': [self.my_hook],  # Add progress hook
        }

        # Add cookies option if the saved preference is True
        if self.cookie_preference:
            ydl_opts['cookies'] = str(self.data_folder / "cookies.txt")  # Specify the path to your cookies file

        # Send the ydl_opts to the Discord channel for debugging
        await ctx.send(f"`ydl_opts: {ydl_opts}`")

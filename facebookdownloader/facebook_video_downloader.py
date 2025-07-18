import discord
from redbot.core import commands
import requests
import re
import os

class FacebookVideoDownloader(commands.Cog):
    """Download Facebook videos via a command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fbvideo(self, ctx, url: str):
        """Download a Facebook video from a public URL and upload it here."""
        async with ctx.typing():
            try:
                video_url, html_content = self.get_facebook_video_url(url, return_html=True)
                if not video_url:
                    # Save HTML to a file and send it for debugging
                    debug_filename = "fb_debug_response.html"
                    with open(debug_filename, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    await ctx.send("Could not find a downloadable video at that URL. Here is the fetched HTML for debugging:", file=discord.File(debug_filename))
                    os.remove(debug_filename)
                    return
                filename = "fb_video.mp4"
                self.download_video(video_url, filename)
                await ctx.send(file=discord.File(filename))
                os.remove(filename)
            except Exception as e:
                await ctx.send(f"Error: {e}")

    def get_facebook_video_url(self, page_url, return_html=False):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(page_url, headers=headers)
        if response.status_code != 200:
            return (None, response.text) if return_html else None
        # Try to find HD or SD video URL in the page source
        hd_match = re.search(r'"hd_src":"(https:[^\"]+)', response.text)
        sd_match = re.search(r'"sd_src":"(https:[^\"]+)', response.text)
        video_url = None
        if hd_match:
            video_url = hd_match.group(1).replace('\\/', '/')
        elif sd_match:
            video_url = sd_match.group(1).replace('\\/', '/')
        if return_html:
            return video_url, response.text
        return video_url

    def download_video(self, video_url, filename):
        response = requests.get(video_url, stream=True)
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk) 
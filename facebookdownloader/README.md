# Facebook Video Downloader Cog for Redbot

This cog allows you to download videos from public Facebook posts directly into your Discord server using Redbot.

## Features
- Download Facebook videos by providing a public post URL.
- Uploads the video directly to the Discord channel.

## Installation
1. Install dependencies:
   ```
pip install -r requirements.txt
   ```
2. Place `facebook_video_downloader.py` in your Redbot's `cogs` directory or load as a custom cog.

## Loading the Cog
In your Discord server, use:
```
[p]load facebook_video_downloader
```
Replace `[p]` with your bot's prefix.

## Usage
```
[p]fbvideo <facebook_video_url>
```
Example:
```
[p]fbvideo https://www.facebook.com/watch/?v=1234567890
```

## Notes
- Only works with public Facebook videos.
- If the video cannot be downloaded, the bot will notify you.
- Facebook may change their page structure, which could break this cog. If it stops working, check for updates or open an issue.

## Disclaimer
This cog is for educational purposes. Downloading videos from Facebook may violate their terms of service. Use responsibly. 
import aiohttp
from redbot.core import commands
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
import urllib.request

class ServerImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='setservericon')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def set_server_icon(self, ctx, url: str = None):
        if url is None and len(ctx.message.attachments) == 0:
            await ctx.send('Error: You must provide either an image URL or upload an image.')
            return

        if url is not None:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as resp:
                        image_bytes = await resp.read()
                        content_type = resp.headers.get('content-type')
                        if content_type in ['image/png', 'image/webp']:
                            await ctx.guild.edit(icon=image_bytes)
                            await ctx.send('Server icon has been updated!')
                        else:
                            await ctx.send('Error: Unsupported image type given.')
                except Exception as e:
                    await ctx.send(f'Error: {str(e)}')

        if len(ctx.message.attachments) > 0:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            image_name = attachment.filename
            if image_name.endswith('.png') or image_name.endswith('.webp'):
                await ctx.guild.edit(icon=image_bytes)
                await ctx.send('Server icon has been updated!')
            else:
                await ctx.send('Error: Unsupported image type given.')
    
    @commands.command()
    async def fakeping(self, ctx):
        # Get the server icon URL
        server = ctx.guild
        icon_url = server.icon_url_as(format='png')
        
        # Open the icon image from URL
        with urllib.request.urlopen(icon_url) as url:
            icon_image = Image.open(url)
            
        # Create a red circle image with the same size as the icon
        circle_image = Image.new('RGBA', icon_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(circle_image)
        draw.ellipse((0, 0, icon_image.size[0], icon_image.size[1]), fill=(255, 0, 0, 128))
        
        # Paste the icon on top of the circle
        result_image = Image.alpha_composite(circle_image, icon_image)
        
        # Save the image to a file
        result_bytes = BytesIO()
        result_image.save(result_bytes, format='PNG')
        result_bytes.seek(0)
        
        # Send the image as an attachment
        await ctx.send(file=discord.File(result_bytes, 'fake_ping.png'))

def setup(bot):
    bot.add_cog(ServerImageCog(bot))

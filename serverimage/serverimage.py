import aiohttp
import discord
from redbot.core import commands
from io import BytesIO
from PIL import Image

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

    @commands.command(name='fakeping')
    @commands.guild_only()
    async def fake_ping(self, ctx):
        icon_url = ctx.guild.icon_url
        if icon_url is None:
            await ctx.send("Server icon is not set.")
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(str(icon_url)) as resp:
                image_bytes = await resp.read()
                image = Image.open(BytesIO(image_bytes))
                image.thumbnail((64, 64))
                image = image.convert('RGBA')
                data = image.getdata()
                new_data = []
                for item in data:
                    if item[3] == 0:
                        new_data.append((0, 0, 0, 0))
                    else:
                        new_data.append(item)
                image.putdata(new_data)
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                file = discord.File(buffer, filename='fake_ping.png')
                await ctx.send(file=file)

def setup(bot):
    bot.add_cog(ServerImageCog(bot))

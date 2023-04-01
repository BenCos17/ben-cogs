import aiohttp
from redbot.core import commands
from io import BytesIO

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

def setup(bot):
    bot.add_cog(ServerImageCog(bot))

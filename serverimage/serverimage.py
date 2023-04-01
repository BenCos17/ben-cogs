import aiohttp
from redbot.core import commands

class ServerImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='setservericon')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def set_server_icon(self, ctx, url: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    image_bytes = await resp.read()
                    content_type = resp.headers.get('content-type')
                    if content_type in ['image/png', 'image/webp']:
                        await ctx.guild.edit(icon=image_bytes)
                        await ctx.send('Server icon has been updated!')
                    else:
                        await ctx.send('Error: Invalid image file format. Only PNG and WEBP files are supported.')
            except Exception as e:
                await ctx.send(f'Error: {str(e)}')

def setup(bot):
    bot.add_cog(ServerImageCog(bot))

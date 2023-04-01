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
                await ctx.guild.edit(icon=image_bytes)
                await ctx.send('Server icon has been updated!')
            except Exception as e:
                await ctx.send(f'Error: {str(e)}')

def setup(bot):
    bot.add_cog(ServerImageCog(bot))

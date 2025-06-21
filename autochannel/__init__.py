from .autochannel import AutoChannel

async def setup(bot):
    await bot.add_cog(AutoChannel(bot))


from .ports import Ports

async def setup(bot):
    await bot.add_cog(Ports(bot))


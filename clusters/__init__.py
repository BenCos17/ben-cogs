from .clusters import Clusters

async def setup(bot):
    await bot.add_cog(Clusters(bot))

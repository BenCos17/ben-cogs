

from .not import Not

async def setup(bot):
    bot.add_cog(Not(bot))

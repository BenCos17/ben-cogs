from redbot.core.bot import Red
from .servercooldown import ServerCooldown


async def setup(bot):
    bot.add_cog(ServerCooldown(bot))

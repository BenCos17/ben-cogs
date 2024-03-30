from .servercooldown import ServerCooldown


async def setup(bot):
    bot.add_cog(ServerCooldown(bot))

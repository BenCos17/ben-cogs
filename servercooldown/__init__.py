from .servercooldown import ServerCooldown


def setup(bot):
    bot.add_cog(ServerCooldown(bot))

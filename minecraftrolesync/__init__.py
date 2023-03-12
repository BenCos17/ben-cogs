from .minecraftrolesync import MinecraftRoleSync


def setup(bot):
    bot.add_cog(MinecraftRoleSync(bot))

from .serverimage import ServerImageCog

def setup(bot):
    bot.add_cog(ServerImageCog(bot))
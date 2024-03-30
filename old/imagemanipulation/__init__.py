from .imagemanipulation  import ImageManipulation


def setup(bot):
    bot.add_cog(ImageManipulation(bot))

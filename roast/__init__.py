from .roast import Roast


def setup(bot):
    bot.add_cog(Roast(bot))

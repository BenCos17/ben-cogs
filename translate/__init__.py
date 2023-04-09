from .translate import TranslateCog

def setup(bot):
    bot.add_cog(TranslateCog(bot))

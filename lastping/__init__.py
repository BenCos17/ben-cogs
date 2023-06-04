from .lastping import LastPing

def setup(bot):
    bot.add_cog(LastPing(bot))
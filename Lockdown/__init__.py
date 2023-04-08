from .lockdown import Lockdown

def setup(bot):
    bot.add_cog(Lockdown(bot))

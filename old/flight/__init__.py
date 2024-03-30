from .flight import Flight

def setup(bot):
    bot.add_cog(Flight(bot))
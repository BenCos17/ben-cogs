from redbot.core import commands
from .impossible_piano import ImpossiblePiano

def setup(bot):
    bot.add_cog(ImpossiblePiano(bot))

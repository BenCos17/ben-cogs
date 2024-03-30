from redbot.core import commands
from .impossible_piano import ImpossiblePiano

async def setup(bot):
    await bot.add_cog(ImpossiblePiano(bot))

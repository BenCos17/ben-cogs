from redbot.core.bot import Red

from .latexnotation import LatexNotation


async def setup(bot: Red):
    bot.add_cog(LatexNotation(bot))

from redbot.core.bot import Red

from .latexnotation import latexnotation


async def setup(bot: Red):
    bot.add_cog(LatexNotation(bot))

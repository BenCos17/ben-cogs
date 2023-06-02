from redbot.core.bot import Red

from .latexnotation import LaTeXNotation


def setup(bot: Red):
    bot.add_cog(LaTeXNotation(bot))

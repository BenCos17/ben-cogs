from redbot.core.bot import Red

from .wordsearch import WordSearch


def setup(bot: Red):
    bot.add_cog(WordSearch(bot))

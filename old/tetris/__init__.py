from .tetris import TetrisCog

def setup(bot):
    cog = TetrisCog(bot)
    bot.add_cog(cog)

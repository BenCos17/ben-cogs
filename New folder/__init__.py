from redbot.core.bot import Red
from .court import Court

def setup(bot: Red):
    cog = Court(bot)
    bot.add_cog(cog)

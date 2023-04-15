from redbot.core import commands

from .userphone import UserPhone


def setup(bot: commands.Bot):
    cog = UserPhone(bot)
    bot.add_cog(cog)

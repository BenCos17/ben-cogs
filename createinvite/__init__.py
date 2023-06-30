from .invitecog import InviteCog

def setup(bot):
    cog = InviteCog(bot)
    bot.add_cog(cog)

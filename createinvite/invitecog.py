import discord
from redbot.core import commands

class InviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def createinvite(self, ctx, max_uses=1, unique=True):
        invite = await ctx.channel.create_invite(max_uses=max_uses, unique=unique)
        await ctx.send(f"Invite created: {invite.url}")

def setup(bot):
    cog = InviteCog(bot)
    bot.add_cog(cog)

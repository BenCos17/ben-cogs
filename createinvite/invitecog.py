import discord
from redbot.core import commands

class InviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def createinvite(self, ctx):
        invite = await ctx.channel.create_invite(max_uses=1, unique=True)
        await ctx.send(f"Invite created: {invite.url}")

def setup(bot):
    bot.add_cog(InviteCog(bot))

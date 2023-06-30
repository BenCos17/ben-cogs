import discord
from redbot.core import commands

class InviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def createinvite(self, ctx, max_uses=1, unique=True, channel=None, reuse_existing=True):
        if not channel:
            channel = ctx.channel
        else:
            channel = discord.utils.get(ctx.guild.channels, name=channel)
        if not channel:
            await ctx.send("Invalid channel name.")
            return

        if max_uses < 0 or max_uses > 100:
            await ctx.send("The maximum uses must be between 0 and 100.")
            return

        if reuse_existing:
            existing_invite = await self.find_existing_invite(channel)
            if existing_invite:
                invite = existing_invite
            else:
                invite = await channel.create_invite(max_uses=max_uses, unique=unique)
        else:
            invite = await channel.create_invite(max_uses=max_uses, unique=unique)
        
        uses_str = "infinite" if max_uses == 0 else str(max_uses)
        action_str = "Updated existing invite" if reuse_existing and existing_invite else "Created new invite"
        await ctx.send(f"{action_str} in {channel.mention} with {uses_str} uses: {invite.url}")

    async def find_existing_invite(self, channel):
        invites = await channel.invites()
        for invite in invites:
            if invite.inviter == self.bot.user:
                return invite
        return None

def setup(bot):
    cog = InviteCog(bot)
    bot.add_cog(cog)

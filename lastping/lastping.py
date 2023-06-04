import discord
from redbot.core import commands

class LastPingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lastping(self, ctx, user: discord.Member):
        channel = ctx.channel
        messages = await channel.history(limit=100).flatten()
        messages.reverse()

        for message in messages:
            mentions = message.mentions
            if user in mentions or discord.utils.get(mentions, id=ctx.guild.id) or discord.utils.get(mentions, id=ctx.guild.default_role.id):
                await ctx.send(f"The last ping from {user.mention} was in message: {message.jump_url}")
                return

        await ctx.send(f"No pings from {user.mention} found in this channel.")

def setup(bot):
    bot.add_cog(LastPingCog(bot))

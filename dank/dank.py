from redbot.core import commands
import random

class Dank(commands.Cog):
    """Gay and Simp rating machine, Dank Memer style."""

    @commands.command()
    async def howgay(self, ctx, user: commands.MemberConverter = None):
        """Shows how gay a user is (random percentage)."""
        if user is None:
            user = ctx.author
        percent = random.randint(0, 100)
        if user == ctx.author:
            await ctx.send(f"gay r8 machine\nYou are {percent}% gay :gay_pride_flag:")
        else:
            await ctx.send(f"gay r8 machine\n{user.display_name} is {percent}% gay :gay_pride_flag:")

    @commands.command()
    async def simprate(self, ctx, user: commands.MemberConverter = None):
        """Shows how much of a simp a user is (random percentage)."""
        if user is None:
            user = ctx.author
        percent = random.randint(0, 100)
        if user == ctx.author:
            await ctx.send(f"simp r8 machine\nYou are {percent}% simp")
        else:
            await ctx.send(f"simp r8 machine\n{user.display_name} is {percent}% simp")






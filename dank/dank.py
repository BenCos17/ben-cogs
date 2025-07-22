from redbot.core import commands
import random
import discord

class Dank(commands.Cog):
    """Gay and Simp rating machine, Dank Memer style."""

    @commands.command()
    async def howgay(self, ctx, user: commands.MemberConverter = None):
        """Shows how gay a user is (random percentage)."""
        if user is None:
            user = ctx.author
        percent = random.randint(0, 100)
        if user == ctx.author:
            desc = f"You are {percent}% gay 🏳️‍🌈"
        else:
            desc = f"{user.display_name} is {percent}% gay 🏳️‍🌈"
        embed = discord.Embed(title="gay r8 machine", description=desc, color=discord.Color.dark_theme())
        await ctx.send(embed=embed)

    @commands.command()
    async def simprate(self, ctx, user: commands.MemberConverter = None):
        """Shows how much of a simp a user is (random percentage)."""
        if user is None:
            user = ctx.author
        percent = random.randint(0, 100)
        if user == ctx.author:
            desc = f"You are {percent}% simp"
        else:
            desc = f"{user.display_name} is {percent}% simp"
        embed = discord.Embed(description=desc, color=discord.Color.dark_theme())
        await ctx.send(embed=embed)






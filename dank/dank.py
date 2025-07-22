from redbot.core import commands
import random
import discord

class Dank(commands.Cog):
    """
    Gay and Simp rating machine, inspired by Dank Memer.

    Provides fun commands to rate how 'gay' or 'simp' a user is, using random percentages.
    The howgay command uses a styled embed similar to Dank Memer, while simprate uses a plain embed.
    """

    @commands.command()
    async def howgay(self, ctx, user: commands.MemberConverter = None):
        """
        Shows how gay a user is (random percentage).

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command was invoked.
        user : discord.Member, optional
            The user to rate. If not provided, rates the command invoker.

        Output
        ------
        Sends an embed with a bold title and a rainbow emoji, showing the gay percentage.
        """
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
        """
        Shows how much of a simp a user is (random percentage).

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command was invoked.
        user : discord.Member, optional
            The user to rate. If not provided, rates the command invoker.

        Output
        ------
        Sends a plain embed showing the simp percentage.
        """
        if user is None:
            user = ctx.author
        percent = random.randint(0, 100)
        if user == ctx.author:
            desc = f"You are {percent}% simp"
        else:
            desc = f"{user.display_name} is {percent}% simp"
        embed = discord.Embed(description=desc, color=discord.Color.dark_theme())
        await ctx.send(embed=embed)






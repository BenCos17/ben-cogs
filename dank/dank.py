import random

import discord
from redbot.core import commands


class Dank(commands.Cog):
    """
    Gay and Simp rating machine, inspired by Dank Memer.

    Provides fun commands to rate how 'gay' or 'simp' a user is, using random percentages.
    The howgay command uses a styled embed similar to Dank Memer, while simprate uses a plain embed.
    """

    @commands.command()
    async def howgay(self, ctx, user: str = None):
        """
        Shows how gay a user is (random percentage).

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command was invoked.
        user : str, optional
            The user to rate. Accepts mention, ID, or name. If not provided, rates the command invoker.

        Output
        ------
        Sends an embed with a bold title and a rainbow emoji, showing the gay percentage.
        """
        target = ctx.author
        if user is not None:
            member = None
            # Try to resolve as a member first
            if ctx.guild:
                member = ctx.guild.get_member_named(user)
                if member is None:
                    try:
                        member = await commands.MemberConverter().convert(ctx, user)
                    except Exception:
                        member = None
            if member is not None:
                target = member
            else:
                # Try to fetch as a user by ID
                try:
                    user_id = int(user.strip('<@!>'))
                    target = await ctx.bot.fetch_user(user_id)
                except Exception:
                    await ctx.send("Could not find that user.")
                    return
        percent = random.randint(0, 100)
        if target == ctx.author:
            desc = f"You are {percent}% gay 🏳️‍🌈"
        else:
            desc = f"{target.display_name if hasattr(target, 'display_name') else target.name} is {percent}% gay 🏳️‍🌈"
        embed = discord.Embed(title="gay r8 machine", description=desc, color=discord.Color.dark_theme())
        await ctx.send(embed=embed)

    @commands.command()
    async def simprate(self, ctx, user: str = None):
        """
        Shows how much of a simp a user is (random percentage).

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command was invoked.
        user : str, optional
            The user to rate. Accepts mention, ID, or name. If not provided, rates the command invoker.

        Output
        ------
        Sends a plain embed showing the simp percentage.
        """
        target = ctx.author
        if user is not None:
            member = None
            # Try to resolve as a member first
            if ctx.guild:
                member = ctx.guild.get_member_named(user)
                if member is None:
                    try:
                        member = await commands.MemberConverter().convert(ctx, user)
                    except Exception:
                        member = None
            if member is not None:
                target = member
            else:
                # Try to fetch as a user by ID
                try:
                    user_id = int(user.strip('<@!>'))
                    target = await ctx.bot.fetch_user(user_id)
                except Exception:
                    await ctx.send("Could not find that user.")
                    return
        percent = random.randint(0, 100)
        if target == ctx.author:
            desc = f"You are {percent}% simp"
        else:
            desc = f"{target.display_name if hasattr(target, 'display_name') else target.name} is {percent}% simp"
        embed = discord.Embed(description=desc, color=discord.Color.dark_theme())
        await ctx.send(embed=embed)






import os
import discord
from redbot.core import commands

class Servertools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def moddm(self, ctx, user: discord.User, *, message):
        if ctx.guild:
            try:
                await user.send(message)
                await ctx.send(f"Message sent to {user.name}")
            except discord.Forbidden:
                await ctx.send("I cannot send a message to this user.")
        else:
            await ctx.send("This command can only be used in a server.")

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core import Config
import random
import discord

class Roast(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  # Replace with a unique identifier
        self.config.register_guild(
            insults=[]
        )

    @commands.group()
    async def roastset(self, ctx):
        """Roast settings"""
        pass

    @roastset.command(name="addinsult")
    @commands.has_permissions(MANAGE_CHANNELS =True)  # Lock command to users with "MANAGE_CHANNELS " permission or above
    async def add_insult(self, ctx, *, insult: str):
        """Add an insult to the list"""
        async with self.config.guild(ctx.guild).insults() as insults:
            insults.append(insult)
        await ctx.send(f"Insult '{insult}' added successfully!")

    @roastset.command(name="removeinsult")
    @commands.has_permissions(kick_members=True)  # Lock command to users with "Kick Members" permission or above
    async def remove_insult(self, ctx, index: int):
        """Remove an insult from the list by its index"""
        async with self.config.guild(ctx.guild).insults() as insults:
            if index < len(insults):
                insult = insults.pop(index)
                await ctx.send(f"Insult '{insult}' removed successfully!")
            else:
                await ctx.send("Invalid index!")

    @commands.command()
    async def roast(self, ctx, user: commands.Greedy[discord.Member]):
        """Roast the specified user"""
        insults = await self.config.guild(ctx.guild).insults()
        if insults:
            insult = random.choice(insults)
            for member in user:
                await ctx.send(f"{member.mention}, {insult}")
        else:
            await ctx.send("No insults available. Add insults using the 'roastset addinsult' command!")


def setup(bot: Red):
    bot.add_cog(Roast(bot))

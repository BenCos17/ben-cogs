import discord
from redbot.core import commands, checks
import asyncio
import random

class Tips(commands.Cog):
    """A cog that displays random tips at intervals."""

    def __init__(self, bot):
        self.bot = bot
        self.tips = [
            "Tip 1: Use `help` command to see all available commands!",
            "Tip 2: Check the documentation for more information.",
            "Tip 3: Use reactions to interact with bot messages.",
            "Tip 4: Commands are case-insensitive.",
            "Tip 5: You can use prefixes to customize your experience.",
        ]
        self.last_tip_time = {}
        self.cooldown = 60
        self.tip_color = discord.Color.blue()
        self.tip_title = "💡 Random Tip"

    @commands.command()
    async def tip(self, ctx):
        """Get a random tip."""
        user_id = ctx.author.id
        current_time = asyncio.get_event_loop().time()

        # Check if user has requested a tip recently (cooldown: 60 seconds)
        if user_id in self.last_tip_time:
            if current_time - self.last_tip_time[user_id] < self.cooldown:
                await ctx.send("You can only get a tip once per minute!")
                return

        self.last_tip_time[user_id] = current_time
        random_tip = random.choice(self.tips)
        
        embed = discord.Embed(
            title="💡 Random Tip",
            description=random_tip,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @checks.is_owner()
    @commands.command()
    async def addtip(self, ctx, *, tip: str):
        """Add a new tip to the list."""
        self.tips.append(tip)
        await ctx.send(f"✅ Tip added! Total tips: {len(self.tips)}")

    @checks.is_owner()
    @commands.command()
    async def removetip(self, ctx, index: int):
        """Remove a tip by index."""
        if 0 <= index < len(self.tips):
            removed = self.tips.pop(index)
            await ctx.send(f"✅ Tip removed: {removed}")
        else:
            await ctx.send("Invalid tip index.")

    @checks.is_owner()
    @commands.command()
    async def tipconfig(self, ctx, setting: str, *, value: str):
        """Configure tip settings (cooldown, color, title)."""
        if setting.lower() == "cooldown":
            try:
                self.cooldown = int(value)
                await ctx.send(f"✅ Cooldown set to {value} seconds.")
            except ValueError:
                await ctx.send("Cooldown must be a number.")
        elif setting.lower() == "color":
            color_map = {
                "blue": discord.Color.blue(),
                "red": discord.Color.red(),
                "green": discord.Color.green(),
            }
            if value.lower() in color_map:
                self.tip_color = color_map[value.lower()]
                await ctx.send(f"✅ Color set to {value}.")
            else:
                await ctx.send("Invalid color.")
        elif setting.lower() == "title":
            self.tip_title = value
            await ctx.send(f"✅ Title set to {value}.")
        else:
            await ctx.send("Invalid setting. Use: cooldown, color, or title.")


async def setup(bot):
    await bot.add_cog(Tips(bot))
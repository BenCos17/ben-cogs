import discord
from redbot.core import commands, checks, Config
import asyncio
import random


class TipSettingsView(discord.ui.View):
    def __init__(self, cog, author_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    def build_embed(self) -> discord.Embed:
        e = discord.Embed(
            title=self.cog.tip_title,
            description="Configure tip settings using the buttons below.",
            color=self.cog.tip_color,
        )
        e.add_field(name="Cooldown (s)", value=str(self.cog.cooldown), inline=False)
        e.add_field(name="Color", value=str(self.cog.tip_color), inline=False)
        e.add_field(name="Total tips", value=str(len(self.cog.tips)), inline=False)
        return e

    @discord.ui.button(label="Cooldown", style=discord.ButtonStyle.primary)
    async def cooldown_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please type the new cooldown in seconds.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.author_id and m.channel == interaction.channel

        try:
            msg = await self.cog.bot.wait_for("message", check=check, timeout=60)
            try:
                self.cog.cooldown = int(msg.content)
                await self.cog.config.cooldown.set(self.cog.cooldown)
                await interaction.followup.send(f"✅ Cooldown set to {msg.content} seconds.", ephemeral=True)
                if interaction.message is not None:
                    await interaction.message.edit(embed=self.build_embed())
            except ValueError:
                await interaction.followup.send("Cooldown must be a number.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out waiting for input.", ephemeral=True)

    @discord.ui.button(label="Color", style=discord.ButtonStyle.secondary)
    async def color_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        color_map = {"blue": discord.Color.blue(), "red": discord.Color.red(), "green": discord.Color.green()}
        await interaction.response.send_message(
            "Please type a color name (blue, red, green).", ephemeral=True
        )

        def check(m: discord.Message):
            return m.author.id == self.author_id and m.channel == interaction.channel

        try:
            msg = await self.cog.bot.wait_for("message", check=check, timeout=60)
            val = msg.content.lower()
            if val in color_map:
                self.cog.tip_color = color_map[val]
                await self.cog.config.tip_color.set(val)
                await interaction.followup.send(f"✅ Color set to {val}.", ephemeral=True)
                if interaction.message is not None:
                    await interaction.message.edit(embed=self.build_embed())
            else:
                await interaction.followup.send("Invalid color.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out waiting for input.", ephemeral=True)

    @discord.ui.button(label="Title", style=discord.ButtonStyle.success)
    async def title_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please type the new title for tips.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.author_id and m.channel == interaction.channel

        try:
            msg = await self.cog.bot.wait_for("message", check=check, timeout=120)
            self.cog.tip_title = msg.content
            await self.cog.config.tip_title.set(msg.content)
            await interaction.followup.send(f"✅ Title set to {msg.content}.", ephemeral=True)
            if interaction.message is not None:
                await interaction.message.edit(embed=self.build_embed())
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out waiting for input.", ephemeral=True)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.message is not None:
            await interaction.message.delete()

class Tips(commands.Cog):
    """A cog that displays random tips at intervals."""

    def __init__(self, bot):
        self.bot = bot
        self.tips = [
            "Tip 1: Use `help` command to see all available commands!",
            "Tip 2: Use reactions or buttons to interact with bot messages.",
            "Tip 3: Commands are case-insensitive.",
            "Tip 4: You can use prefixes to customize your experience.",
        ]
        self.last_tip_time = {}
        # Config setup
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_global = {
            "cooldown": 60,
            "tip_color": "blue",
            "tip_title": "💡 Random Tip",
            "tips": self.tips,
        }
        self.config.register_global(**default_global)

        # Runtime values (will be loaded from config in cog_load)
        self.cooldown = 60
        self.tip_color = discord.Color.blue()
        self.tip_title = "💡 Random Tip"

    @commands.command()
    async def tip(self, ctx):
        """Get a random tip."""
        # Refresh runtime values from config
        try:
            self.cooldown = await self.config.cooldown()
            color_name = await self.config.tip_color()
            color_map = {"blue": discord.Color.blue(), "red": discord.Color.red(), "green": discord.Color.green()}
            self.tip_color = color_map.get(color_name, discord.Color.blue())
            self.tip_title = await self.config.tip_title()
            self.tips = await self.config.tips()
        except Exception:
            pass
        user_id = ctx.author.id
        current_time = asyncio.get_event_loop().time()

        # Check if user has requested a tip recently (cooldown: 60 seconds)
        if user_id in self.last_tip_time:
            if current_time - self.last_tip_time[user_id] < self.cooldown:
                await ctx.send("You can only get a tip once per minute!")
                return

        self.last_tip_time[user_id] = current_time
        random_tip = random.choice(self.tips) if self.tips else "No tips available."

        embed = discord.Embed(
            title=self.tip_title,
            description=random_tip,
            color=self.tip_color,
        )
        await ctx.send(embed=embed)

    @checks.is_owner()
    @commands.command()
    async def addtip(self, ctx, *, tip: str):
        """Add a new tip to the list."""
        self.tips.append(tip)
        await self.config.tips.set(self.tips)
        await ctx.send(f"✅ Tip added! Total tips: {len(self.tips)}")

    @checks.is_owner()
    @commands.command()
    async def removetip(self, ctx, index: int):
        """Remove a tip by index."""
        if 0 <= index < len(self.tips):
            removed = self.tips.pop(index)
            await self.config.tips.set(self.tips)
            await ctx.send(f"✅ Tip removed: {removed}")
        else:
            await ctx.send("Invalid tip index.")

    @checks.is_owner()
    @commands.command()
    async def tipconfig(self, ctx):
        """Open a button-style settings menu for tips."""
        view = TipSettingsView(self, ctx.author.id)
        embed = discord.Embed(
            title=self.tip_title,
            description="Configure tip settings using the buttons below.",
            color=self.tip_color,
        )
        embed.add_field(name="Cooldown (s)", value=str(self.cooldown), inline=False)
        embed.add_field(name="Color", value=str(self.tip_color), inline=False)
        embed.add_field(name="Total tips", value=str(len(self.tips)), inline=False)
        await ctx.send(embed=embed, view=view)

    async def cog_load(self) -> None:
        """Load values from config into runtime attributes."""
        try:
            self.cooldown = await self.config.cooldown()
            color_name = await self.config.tip_color()
            color_map = {"blue": discord.Color.blue(), "red": discord.Color.red(), "green": discord.Color.green()}
            self.tip_color = color_map.get(color_name, discord.Color.blue())
            self.tip_title = await self.config.tip_title()
            self.tips = await self.config.tips()
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(Tips(bot))
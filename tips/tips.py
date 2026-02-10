import discord
from redbot.core import commands, checks, Config
import asyncio
import random
from typing import Optional


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
            "post_on_command": True,
        }
        default_guild = {"cooldown": None, "post_on_command": None}
        default_user = {"cooldown": None}
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

        # Runtime values (will be loaded from config in cog_load)
        self.cooldown = 60
        self.tip_color = discord.Color.blue()
        self.tip_title = "💡 Random Tip"

    @commands.command()
    async def tip(self, ctx):
        """Get a random tip."""
        # Refresh runtime values from config
        try:
            # Refresh runtime values from config (global values and tips list)
            self.tip_title = await self.config.tip_title()
            color_name = await self.config.tip_color()
            color_map = {"blue": discord.Color.blue(), "red": discord.Color.red(), "green": discord.Color.green()}
            self.tip_color = color_map.get(color_name, discord.Color.blue())
            self.tips = await self.config.tips()
        except Exception:
            pass
        user_id = ctx.author.id
        current_time = asyncio.get_event_loop().time()
        # Determine effective cooldown (user -> guild -> global)
        effective_cd = await self._get_effective_cooldown(ctx.author, ctx.guild)
        key = (user_id, ctx.guild.id if ctx.guild else None)

        last = self.last_tip_time.get(key, 0)
        if current_time - last < (effective_cd or 0):
            await ctx.send(f"You can only get a tip once every {effective_cd} seconds.")
            return

        self.last_tip_time[key] = current_time
        random_tip = random.choice(self.tips) if self.tips else "No tips available."

        embed = discord.Embed(
            title=self.tip_title,
            description=random_tip,
            color=self.tip_color,
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Listener: when any command is run, optionally post a tip to the same channel.

        Respects guild/global `post_on_command` setting and the same cooldown resolution.
        """
        # Ignore commands from bots or from this cog to avoid recursion
        if ctx.author.bot:
            return
        if ctx.cog and getattr(ctx.cog, "__class__", None) is not None and ctx.cog.qualified_name == getattr(self, "qualified_name", "Tips"):
            return

        # Decide whether we should post for this context
        should = await self._should_post_on_command(ctx.guild)
        if not should:
            return

        # Use the same cooldown rules and attempt to post
        effective_cd = await self._get_effective_cooldown(ctx.author, ctx.guild)
        user_id = ctx.author.id
        current_time = asyncio.get_event_loop().time()
        key = (user_id, ctx.guild.id if ctx.guild else None)
        last = self.last_tip_time.get(key, 0)
        if current_time - last < (effective_cd or 0):
            return

        # Send a tip
        random_tip = random.choice(self.tips) if self.tips else None
        if not random_tip:
            return
        embed = discord.Embed(title=self.tip_title, description=random_tip, color=self.tip_color)
        await ctx.channel.send(embed=embed)
        self.last_tip_time[key] = current_time

    async def _should_post_on_command(self, guild: Optional[discord.Guild]) -> bool:
        """Resolve whether to post a tip when a command runs (guild override -> global)."""
        try:
            if guild is not None:
                guild_val = await self.config.guild(guild).post_on_command()
            else:
                guild_val = None
        except Exception:
            guild_val = None
        if guild_val is not None:
            return bool(guild_val)
        try:
            return bool(await self.config.post_on_command())
        except Exception:
            return False

    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def disablepostoncommand(self, ctx):
        """Disable posting tips automatically when commands are run in this server."""
        await self.config.guild(ctx.guild).post_on_command.set(False)
        await ctx.send("✅ Disabled automatic tip posts on commands for this server.")

    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def enablepostoncommand(self, ctx):
        """Enable posting tips automatically when commands are run in this server."""
        await self.config.guild(ctx.guild).post_on_command.set(True)
        await ctx.send("✅ Enabled automatic tip posts on commands for this server.")

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
    @checks.is_owner()
    @commands.command(name="tipset")
    async def tipset(self, ctx):
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
            # Refresh runtime values from config
            self.tip_title = await self.config.tip_title()
            color_name = await self.config.tip_color()
            color_map = {"blue": discord.Color.blue(), "red": discord.Color.red(), "green": discord.Color.green()}
            self.tip_color = color_map.get(color_name, discord.Color.blue())
            self.tips = await self.config.tips()
        except Exception:
            pass

    async def _get_effective_cooldown(self, user: discord.User, guild: Optional[discord.Guild]) -> int:
        """Resolve cooldown with priority: user -> guild -> global."""
        try:
            user_cd = await self.config.user(user).cooldown()
        except Exception:
            user_cd = None
        if user_cd is not None:
            return int(user_cd)
        try:
            if guild:
                guild_cd = await self.config.guild(guild).cooldown()
            else:
                guild_cd = None
        except Exception:
            guild_cd = None
        if guild_cd is not None:
            return int(guild_cd)
        try:
            global_cd = await self.config.cooldown()
            return int(global_cd)
        except Exception:
            return 0

    @commands.command()
    async def setmycooldown(self, ctx, seconds: int):
        """Set a personal cooldown (affects only you across servers)."""
        if seconds < 0:
            await ctx.send("Cooldown cannot be negative.")
            return
        await self.config.user(ctx.author).cooldown.set(seconds)
        await ctx.send(f"✅ Your personal tip cooldown is now {seconds} seconds.")

    @commands.command()
    async def clearmycooldown(self, ctx):
        """Clear your personal cooldown override."""
        await self.config.user(ctx.author).cooldown.set(None)
        await ctx.send("✅ Your personal tip cooldown override has been cleared.")

    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def setguildcooldown(self, ctx, seconds: int):
        """Set a guild-wide cooldown (affects all users in this server)."""
        if seconds < 0:
            await ctx.send("Cooldown cannot be negative.")
            return
        await self.config.guild(ctx.guild).cooldown.set(seconds)
        await ctx.send(f"✅ Server tip cooldown set to {seconds} seconds.")

    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def clearguildcooldown(self, ctx):
        """Clear the guild-wide cooldown override."""
        await self.config.guild(ctx.guild).cooldown.set(None)
        await ctx.send("✅ Server tip cooldown override cleared.")


async def setup(bot):
    await bot.add_cog(Tips(bot))
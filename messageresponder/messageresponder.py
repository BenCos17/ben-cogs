import discord
from redbot.core import commands, Config
from discord.ui import Modal, TextInput, View

class TriggerModal(Modal, title="Add New Trigger"):
    trigger = TextInput(label="Trigger Word", style=discord.TextStyle.short, placeholder="e.g. hello", required=True)
    response = TextInput(label="Response", style=discord.TextStyle.paragraph, placeholder="e.g. Hi there!", required=True)

    def __init__(self, cog, guild: discord.Guild):
        super().__init__()
        self.cog = cog
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        async with self.cog.config.guild(self.guild).triggers() as triggers:
            triggers[self.trigger.value.lower()] = self.response.value
        await interaction.response.send_message(f"✅ Trigger '{self.trigger.value}' added for this server!", ephemeral=True)

class TriggerButtonView(View):
    def __init__(self, cog, guild: discord.Guild):
        super().__init__(timeout=60)
        self.cog = cog
        self.guild = guild

    @discord.ui.button(label="Open Trigger Form", style=discord.ButtonStyle.primary, emoji="📝")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TriggerModal(self.cog, self.guild))

class MessageResponder(commands.Cog):
    """Responds to specific keywords in messages."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        self.config.register_guild(triggers={})

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        content = message.content.lower()
        triggers = await self.config.guild(message.guild).triggers()
        for trigger, response in triggers.items():
            if trigger in content:
                await message.channel.send(response)
                break 

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def responder(self, ctx):
        """Manage custom triggers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @commands.hybrid_command(name="responderui")
    @commands.guild_only()
    async def ui_add_trigger(self, ctx: commands.Context):
        """Open a UI to add a new trigger."""
        view = TriggerButtonView(self, ctx.guild)
        
        if ctx.interaction:
            # If used via slash command, send the modal directly or via a ephemeral response with view
            await ctx.interaction.response.send_modal(TriggerModal(self, ctx.guild))
        else:
            # If used via prefix command, send a button message since prefix commands can't trigger modals directly
            await ctx.send(
                "Click the button below to open the trigger creation form:", 
                view=view, 
                delete_after=60
            )

    @responder.command(name="add")
    @commands.guild_only()
    async def add_trigger(self, ctx, trigger: str, *, response: str):
        """Add a custom trigger via command."""
        async with self.config.guild(ctx.guild).triggers() as triggers:
            triggers[trigger.lower()] = response
        await ctx.send(f"✅ Trigger added: '{trigger}'")

    @responder.command(name="remove")
    @commands.guild_only()
    async def remove_trigger(self, ctx, trigger: str):
        """Remove a custom trigger."""
        async with self.config.guild(ctx.guild).triggers() as triggers:
            if trigger.lower() in triggers:
                del triggers[trigger.lower()]
                await ctx.send(f"🗑️ Trigger '{trigger}' removed.")
            else:
                await ctx.send("❌ Trigger not found.")

    @responder.command(name="list")
    @commands.guild_only()
    async def list_triggers(self, ctx):        
        """List all custom triggers."""
        triggers = await self.config.guild(ctx.guild).triggers()
        if not triggers:
            await ctx.send("No triggers set for this server.")
            return

        embed = discord.Embed(
            title="📜 Current Server Triggers",
            color=await ctx.embed_color()
        )
        
        trigger_list = "\n".join(f"**{t}**: {r}" for t, r in triggers.items())
        embed.description = trigger_list[:4096]
        
        await ctx.send(
            embed=embed, 
            allowed_mentions=discord.AllowedMentions.none()
        )
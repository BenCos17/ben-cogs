import discord
from redbot.core import commands, Config
from discord.ui import Modal, TextInput

class TriggerModal(Modal, title="Add New Trigger"):
    trigger = TextInput(label="Trigger Word", style=discord.TextStyle.short, placeholder="e.g. hello", required=True)
    response = TextInput(label="Response", style=discord.TextStyle.paragraph, placeholder="e.g. Hi there!", required=True)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        async with self.cog.config.triggers() as triggers:
            triggers[self.trigger.value.lower()] = self.response.value
        await interaction.response.send_message(f"✅ Trigger '{self.trigger.value}' added!", ephemeral=True)

class MessageResponder(commands.Cog):
    """Responds to specific keywords in messages."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        self.config.register_global(triggers={})

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
        # Checks if the message is a command. If so, do not trigger auto-responses.
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        content = message.content.lower()
        triggers = await self.config.triggers()
        for trigger, response in triggers.items():
            if trigger in content:
                # Pinging allowed in auto-responses
                await message.channel.send(response)
                break 
        
        # I don't need process_commands here because get_context 
        # already checked if it was a command, and the bot 
        # handles the command execution separately

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def responder(self, ctx):
        """Manage custom triggers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @commands.hybrid_command(name="responderui")
    async def ui_add_trigger(self, ctx: commands.Context):
        """Open a UI to add a new trigger."""
        # Check if this is being called as a slash command
        if ctx.interaction:
            await ctx.interaction.response.send_modal(TriggerModal(self))
        else:
            # If called as a prefix command, tell the user to use slash
            await ctx.send("Please use the slash command `/responderui` to open the UI.")

    @responder.command(name="add")
    async def add_trigger(self, ctx, trigger: str, *, response: str):
        """Add a custom trigger via command."""
        async with self.config.triggers() as triggers:
            triggers[trigger.lower()] = response
        await ctx.send(f"✅ Trigger added: '{trigger}'")

    @responder.command(name="remove")
    async def remove_trigger(self, ctx, trigger: str):
        """Remove a custom trigger."""
        async with self.config.triggers() as triggers:
            if trigger.lower() in triggers:
                del triggers[trigger.lower()]
                await ctx.send(f"🗑️ Trigger '{trigger}' removed.")
            else:
                await ctx.send("❌ Trigger not found.")

    @responder.command(name="list")
    async def list_triggers(self, ctx):        
        """List all custom triggers."""
        triggers = await self.config.triggers()
        if not triggers:
            await ctx.send("No triggers set.")
            return

        # Build the embed
        embed = discord.Embed(
            title="📜 Current Triggers",
            color=await ctx.embed_color()
        )
        
        trigger_list = "\n".join(f"**{t}**: {r}" for t, r in triggers.items())
        embed.description = trigger_list[:4096]
        
        # Send with allowed_mentions=none to prevent pings in the list output
        await ctx.send(
            embed=embed, 
            allowed_mentions=discord.AllowedMentions.none()
        )
import discord
from redbot.core import commands, Config

class MessageResponder(commands.Cog):
    """Responds to specific keywords in messages."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(triggers={})

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.lower()
        triggers = await self.config.triggers()

        for trigger, response in triggers.items():
            if trigger in content:
                await message.channel.send(response)
                break 
        
        await self.bot.process_commands(message)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def responder(self, ctx):
        """Manage custom triggers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @responder.command(name="add")
    async def add_trigger(self, ctx, trigger: str, *, response: str):
        """Add a custom trigger."""
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

        trigger_list = "\n".join(f"**{trigger}**: {response}" for trigger, response in triggers.items())
        await ctx.send(f"📜 Current triggers:\n{trigger_list}")
import discord
from redbot.core import commands, Config

class MessageResponder(commands.Cog):
    """Responds to specific keywords in messages."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890) # Use a unique ID
        self.config.register_global(triggers={})

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.lower()
        triggers = await self.config.triggers()

        for trigger, response in triggers.items():
            if trigger in content:
                await message.channel.send(response)
                break 

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def responder(self, ctx):
        """Manage custom triggers."""
        pass

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
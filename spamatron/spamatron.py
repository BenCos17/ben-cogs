from redbot.core import commands
import discord

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def parse_channel_mention(self, ctx, channel_mention):
        if not channel_mention.startswith("<#") or not channel_mention.endswith(">"):
            return None

        channel_id = int(channel_mention[2:-1])
        return ctx.guild.get_channel(channel_id)

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_confirmation(self, ctx, confirmation_message: str):
        """Set your custom confirmation message for spam."""
        await self.bot.get_cog("Spamatron").config.user(ctx.author).confirmation_message.set(confirmation_message)
        await ctx.send("Custom confirmation message set successfully.")

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, "config"):
            raise RuntimeError("Config is required for this cog to work.")
        await self.bot.wait_until_ready()
        self.config = self.bot.get_cog("Config")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel_mention: str, amount: int, *, message: str):
        """Spam a message in a channel a specified number of times."""
        target_channel = await self.parse_channel_mention(ctx, channel_mention)
        if not target_channel:
            return await ctx.send("Invalid channel mention.")

        if amount <= 0:
            return await ctx.send("Please provide a positive number for the amount.")

        confirmation_message = await self.bot.get_cog("Spamatron").config.user(ctx.author).confirmation_message()
        if not confirmation_message:
            confirmation_message = "Are you sure you want to send this message?"

        confirmation = await ctx.send(confirmation_message)

        try:
            reply = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.lower() == "yes",
                timeout=30,
            )
        except TimeoutError:
            return await ctx.send("Confirmation timed out. Aborting.")

        for _ in range(amount):
            await target_channel.send(message)

        await ctx.send(f"Successfully sent `{amount}` messages to {target_channel.mention}.")

def setup(bot):
    bot.add_cog(Spamatron(bot))

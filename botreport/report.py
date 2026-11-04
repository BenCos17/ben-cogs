import discord
from redbot.core import Config, commands
from redbot.core.bot import Red


class BotReport(commands.Cog):
    """Let members report messages to a moderator channel."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        self.config.register_global(report_channel=None)

    @staticmethod
    def _truncate(value: str, limit: int) -> str:
        value = value or ""
        return value if len(value) <= limit else f"{value[: limit - 3]}..."

    async def _get_reported_message(self, ctx: commands.Context) -> discord.Message | None:
        reference = ctx.message.reference
        if reference is None or reference.message_id is None:
            return None
        if isinstance(reference.resolved, discord.Message):
            return reference.resolved
        try:
            return await ctx.channel.fetch_message(reference.message_id)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            return None

    @commands.command(name="botreport")
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def report(self, ctx: commands.Context, *, reason: str = "No reason provided."):
        """Report the message this command is replying to."""
        channel_id = await self.config.report_channel()
        report_channel = self.bot.get_channel(channel_id) if channel_id else None
        if not isinstance(report_channel, discord.TextChannel):
            await ctx.send("Reports are not configured. Ask the bot owner to run `[p]botreportset channel #channel`.")
            return

        message = await self._get_reported_message(ctx)
        if message is None:
            await ctx.send("Reply to the message you want to report, then run `[p]botreport <reason>`.")
            return

        embed = discord.Embed(
            title="Message reported",
            description=self._truncate(message.content, 4096) or "(no text content)",
            color=discord.Color.red(),
            timestamp=message.created_at,
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="Reported by", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
        embed.add_field(name="Original author", value=f"{message.author.mention} (`{message.author.id}`)", inline=True)
        embed.add_field(name="Reason", value=self._truncate(reason, 1024), inline=False)
        embed.add_field(name="Message", value=f"[Jump to message]({message.jump_url})", inline=False)
        if message.attachments:
            attachments = "\n".join(attachment.url for attachment in message.attachments)
            embed.add_field(name="Attachments", value=self._truncate(attachments, 1024), inline=False)
            first_attachment = message.attachments[0]
            if first_attachment.content_type and first_attachment.content_type.startswith("image/"):
                embed.set_image(url=first_attachment.url)

        try:
            await report_channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            await ctx.send("I cannot send reports to the configured channel. Ask a moderator to check my permissions.")
            return

        await ctx.send("Your report was sent to the moderators.")

    @commands.group(name="botreportset", invoke_without_command=True)
    @commands.guild_only()
    @commands.is_owner()
    async def reportset(self, ctx: commands.Context):
        """Configure the global channel used for message reports."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @reportset.command(name="channel")
    async def reportset_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the global channel where reports should be sent."""
        await self.config.report_channel.set(channel.id)
        await ctx.send(f"Reports from all servers will be sent to {channel.mention}.")

    @reportset.command(name="disable")
    async def reportset_disable(self, ctx: commands.Context):
        """Disable message reports globally."""
        await self.config.report_channel.clear()
        await ctx.send("Message reports are disabled globally.")

    @reportset.command(name="status")
    async def reportset_status(self, ctx: commands.Context):
        """Show the global report channel."""
        channel_id = await self.config.report_channel()
        channel = self.bot.get_channel(channel_id) if channel_id else None
        await ctx.send(f"Global reports are configured for {channel.mention}." if channel else "Global reports are not configured.")
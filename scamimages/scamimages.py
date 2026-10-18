from __future__ import annotations

import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
import discord
import imagehash
from PIL import Image
from redbot.core import Config, commands, modlog


API_URL = "https://api.excessive.space/v1/scamscore"
DEFAULT_THRESHOLD = 4
DEFAULT_USER_AGENT = "ScamImages/1.0.0"
DEFAULT_TIMEOUT_SECONDS = 3600
MAX_TIMEOUT_SECONDS = 28 * 24 * 60 * 60
log = logging.getLogger("red.ScamImages")


class ScamImages(commands.Cog):
    """Detect known scam images in opted-in servers."""

    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976, force_registration=True)
        self.config.register_global(user_agent=DEFAULT_USER_AGENT)
        self.config.register_guild(
            enabled=False,
            threshold=DEFAULT_THRESHOLD,
            delete_matches=True,
            timeout_members=True,
            timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
            modlog_enabled=True,
            notify_channel=False,
            ignored_channels=[],
        )
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session is not None:
            await self.session.close()
            self.session = None

    @commands.group(name="scamimages", invoke_without_command=True)
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def scamimages(self, ctx):
        """Configure scam image detection for this server."""
        await ctx.send_help(ctx.command)

    @scamimages.command(name="enable")
    async def scamimages_enable(self, ctx):
        """Opt this server in to scam image detection."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Scam image detection is now enabled.")

    @scamimages.command(name="disable")
    async def scamimages_disable(self, ctx):
        """Opt this server out of scam image detection."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Scam image detection is now disabled.")

    @scamimages.command(name="status")
    async def scamimages_status(self, ctx):
        """Show this server's scam image settings."""
        settings = await self.config.guild(ctx.guild).all()
        state = "enabled" if settings["enabled"] else "disabled"
        user_agent = await self.config.user_agent()
        await ctx.send(
            f"Scam image detection is **{state}**. "
            f"Threshold: **{settings['threshold']}**. "
            f"Delete: **{settings['delete_matches']}**. "
            f"Timeout: **{settings['timeout_members']}** "
            f"({settings['timeout_seconds']}s). "
            f"Modlog: **{settings['modlog_enabled']}**. "
            f"Channel notice: **{settings['notify_channel']}**. "
            f"Hidden channels: **{len(settings['ignored_channels'])}**. "
            f"User-Agent: `{user_agent}`."
        )

    @scamimages.command(name="threshold")
    async def scamimages_threshold(self, ctx, threshold: int):
        """Set the minimum score that counts as a hit (1-10)."""
        if not 1 <= threshold <= 10:
            await ctx.send("The threshold must be between 1 and 10.")
            return
        await self.config.guild(ctx.guild).threshold.set(threshold)
        await ctx.send(f"Scam image hit threshold set to **{threshold}**.")

    @scamimages.command(name="delete")
    async def scamimages_delete(self, ctx, enabled: bool):
        """Choose whether detected scam images should be deleted."""
        await self.config.guild(ctx.guild).delete_matches.set(enabled)
        state = "will" if enabled else "will not"
        await ctx.send(f"Detected scam image messages {state} be deleted.")

    @scamimages.command(name="timeout")
    async def scamimages_timeout(self, ctx, enabled: bool):
        """Choose whether users should be timed out for detected images."""
        await self.config.guild(ctx.guild).timeout_members.set(enabled)
        state = "will" if enabled else "will not"
        await ctx.send(f"Users who post detected scam images {state} be timed out.")

    @scamimages.command(name="timeoutduration")
    async def scamimages_timeoutduration(self, ctx, seconds: int):
        """Set the timeout duration in seconds (60 seconds to 28 days)."""
        if not 60 <= seconds <= MAX_TIMEOUT_SECONDS:
            await ctx.send(
                f"The timeout duration must be between 60 and {MAX_TIMEOUT_SECONDS} seconds."
            )
            return
        await self.config.guild(ctx.guild).timeout_seconds.set(seconds)
        await ctx.send(f"Scam image timeout duration set to **{seconds} seconds**.")

    @scamimages.command(name="modlog")
    async def scamimages_modlog(self, ctx, enabled: bool):
        """Choose whether detections create Redbot modlog cases."""
        await self.config.guild(ctx.guild).modlog_enabled.set(enabled)
        state = "will" if enabled else "will not"
        await ctx.send(f"Detections {state} be sent to the Redbot modlog.")

    @scamimages.command(name="notify")
    async def scamimages_notify(self, ctx, enabled: bool):
        """Choose whether detections also post in the source channel."""
        await self.config.guild(ctx.guild).notify_channel.set(enabled)
        state = "will" if enabled else "will not"
        await ctx.send(f"Detections {state} post a notice in the source channel.")

    @scamimages.command(name="useragent")
    @commands.is_owner()
    async def scamimages_useragent(self, ctx, *, user_agent: str = ""):
        """Set the global API User-Agent, or reset it by omitting the value."""
        user_agent = user_agent.strip()
        if "\r" in user_agent or "\n" in user_agent:
            await ctx.send("The User-Agent cannot contain line breaks.")
            return
        if len(user_agent) > 256:
            await ctx.send("The User-Agent must be 256 characters or fewer.")
            return
        if not user_agent:
            user_agent = DEFAULT_USER_AGENT
        await self.config.user_agent.set(user_agent)
        await ctx.send(f"Global API User-Agent set to `{user_agent}`.")

    @scamimages.command(name="hide")
    async def scamimages_hide(self, ctx, channel: discord.TextChannel):
        """Hide a channel from scam image detection."""
        ignored_channels = await self.config.guild(ctx.guild).ignored_channels()
        if channel.id not in ignored_channels:
            ignored_channels.append(channel.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
        await ctx.send(f"Scam image detection is hidden in {channel.mention}.")

    @scamimages.command(name="unhide")
    async def scamimages_unhide(self, ctx, channel: discord.TextChannel):
        """Allow scam image detection in a previously hidden channel."""
        ignored_channels = await self.config.guild(ctx.guild).ignored_channels()
        if channel.id in ignored_channels:
            ignored_channels.remove(channel.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
        await ctx.send(f"Scam image detection is enabled in {channel.mention}.")

    @scamimages.command(name="hidden")
    async def scamimages_hidden(self, ctx):
        """List channels hidden from scam image detection."""
        ignored_channels = await self.config.guild(ctx.guild).ignored_channels()
        channels = [ctx.guild.get_channel(channel_id) for channel_id in ignored_channels]
        mentions = [channel.mention for channel in channels if channel is not None]
        await ctx.send(
            "Hidden channels: " + (", ".join(mentions) if mentions else "none.")
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        guild_config = self.config.guild(message.guild)
        if not await guild_config.enabled():
            return
        if message.channel.id in await guild_config.ignored_channels():
            return

        image_attachments = self._collect_image_attachments(message)
        if not image_attachments:
            return

        for attachment in image_attachments:
            result = await self._check_attachment(attachment, message.guild)
            if result is None:
                continue
            score, error = result
            if error is not None:
                await self._report_error(message, error)
                continue
            threshold = await self.config.guild(message.guild).threshold()
            if score is not None and score >= threshold:
                await self._handle_match(message, attachment, score)

    @staticmethod
    def _is_image_attachment(attachment: Any) -> bool:
        content_type = str(getattr(attachment, "content_type", "") or "").lower()
        if content_type.startswith("image/"):
            return True
        filename = str(getattr(attachment, "filename", "") or "").lower()
        return filename.endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
        )

    def _collect_image_attachments(self, message: discord.Message) -> list[Any]:
        image_attachments: list[Any] = []
        seen_attachments: set[tuple[Any, ...]] = set()

        for attachment in getattr(message, "attachments", ()) or ():
            self._add_image_attachment(attachment, image_attachments, seen_attachments)

        try:
            snapshots = getattr(message, "message_snapshots", ()) or ()
            for snapshot in snapshots:
                for attachment in getattr(snapshot, "attachments", ()) or ():
                    self._add_image_attachment(attachment, image_attachments, seen_attachments)
        except TypeError:
            pass

        return image_attachments

    def _add_image_attachment(
        self, attachment: Any, image_attachments: list[Any], seen_attachments: set[tuple[Any, ...]]
    ) -> None:
        if not self._is_image_attachment(attachment):
            return
        key = self._attachment_dedupe_key(attachment)
        if key in seen_attachments:
            return
        seen_attachments.add(key)
        image_attachments.append(attachment)

    @staticmethod
    def _attachment_dedupe_key(attachment: Any) -> tuple[Any, ...]:
        attachment_id = getattr(attachment, "id", None)
        if attachment_id is not None:
            return ("id", attachment_id)
        return (
            "fallback",
            getattr(attachment, "url", None),
            getattr(attachment, "filename", None),
            getattr(attachment, "size", None),
            getattr(attachment, "content_type", None),
        )

    async def _check_attachment(
        self, attachment: Any, guild: discord.Guild
    ) -> tuple[int | None, str | None] | None:
        filename = str(getattr(attachment, "filename", "attachment"))
        try:
            image_data = await attachment.read()
            with Image.open(io.BytesIO(image_data)) as image:
                image_hash = str(imagehash.phash(image, hash_size=16))
        except (AttributeError, TypeError, discord.HTTPException, OSError, ValueError) as exc:
            return None, f"could not read `{filename}` ({exc})"

        if self.session is None:
            return None

        try:
            async with self.session.get(
                API_URL,
                params={"hash": image_hash, "dimensions": f"{image.width},{image.height}"},
                headers={"User-Agent": await self.config.user_agent()},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                payload: dict[str, Any] = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            return None, f"the scam image service was unavailable ({exc})"

        if "error" in payload:
            return None, str(payload["error"])
        try:
            return int(payload["result"]), None
        except (KeyError, TypeError, ValueError):
            return None, "the scam image service returned an invalid response"

    async def _handle_match(
        self, message: discord.Message, attachment: Any, score: int
    ):
        settings = await self.config.guild(message.guild).all()
        attachment_url = getattr(attachment, "url", "unknown-url")
        reason = f"Scam image detected (score {score}/10): {attachment_url}"
        deleted = False
        if settings["delete_matches"]:
            try:
                await message.delete()
                deleted = True
            except discord.HTTPException:
                pass

        timed_out = False
        if settings["timeout_members"] and isinstance(message.author, discord.Member):
            try:
                await message.author.timeout(
                    timedelta(seconds=settings["timeout_seconds"]), reason=reason
                )
                timed_out = True
            except discord.HTTPException:
                log.exception("Failed to timeout %s for a scam image", message.author)

        if settings["modlog_enabled"]:
            try:
                await modlog.create_case(
                    self.bot,
                    message.guild,
                    datetime.now(timezone.utc),
                    "warning",
                    message.author,
                    self.bot.user,
                    reason,
                    message.channel,
                )
            except (discord.HTTPException, RuntimeError):
                log.exception("Failed to create a modlog case for a scam image")

        if settings["notify_channel"]:
            actions = []
            if deleted:
                actions.append("deleted")
            if timed_out:
                actions.append("user timed out")
            action = " and ".join(actions) or "flagged"
            await message.channel.send(
                f"Scam image {action} (score **{score}/10**).", delete_after=30
            )

    @staticmethod
    async def _report_error(message: discord.Message, error: str):
        await message.channel.send(
            f"I could not check an image in that message: {error}", delete_after=30
        )

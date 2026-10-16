from __future__ import annotations

import io
from typing import Any

import aiohttp
import discord
import imagehash
from PIL import Image
from redbot.core import Config, commands


API_URL = "https://api.excessive.space/v1/scamscore"
DEFAULT_THRESHOLD = 4


class ScamImages(commands.Cog):
    """Detect known scam images in opted-in servers."""

    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976, force_registration=True)
        self.config.register_guild(
            enabled=False,
            threshold=DEFAULT_THRESHOLD,
            delete_matches=False,
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
        action = "delete and report" if settings["delete_matches"] else "report only"
        state = "enabled" if settings["enabled"] else "disabled"
        await ctx.send(
            f"Scam image detection is **{state}**. "
            f"Hit threshold: **{settings['threshold']}**. Action: **{action}**."
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
        state = "will be deleted" if enabled else "will only be reported"
        await ctx.send(f"Detected scam images {state}.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        if not await self.config.guild(message.guild).enabled():
            return

        image_attachments = [
            attachment
            for attachment in message.attachments
            if self._is_image_attachment(attachment)
        ]
        if not image_attachments:
            return

        for attachment in image_attachments:
            result = await self._check_attachment(attachment)
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
    def _is_image_attachment(attachment: discord.Attachment) -> bool:
        content_type = (attachment.content_type or "").lower()
        if content_type.startswith("image/"):
            return True
        return attachment.filename.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
        )

    async def _check_attachment(
        self, attachment: discord.Attachment
    ) -> tuple[int | None, str | None] | None:
        try:
            image_data = await attachment.read()
            with Image.open(io.BytesIO(image_data)) as image:
                image_hash = str(imagehash.phash(image, hash_size=16))
        except (discord.HTTPException, OSError, ValueError) as exc:
            return None, f"could not read `{attachment.filename}` ({exc})"

        if self.session is None:
            return None

        try:
            async with self.session.get(
                API_URL,
                params={"hash": image_hash, "dimensions": f"{image.width},{image.height}"},
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
        self, message: discord.Message, attachment: discord.Attachment, score: int
    ):
        deleted = False
        if await self.config.guild(message.guild).delete_matches():
            try:
                await message.delete()
                deleted = True
            except discord.HTTPException:
                pass

        action = "deleted" if deleted else "flagged"
        await message.channel.send(
            f"Scam image {action} (score **{score}/10**): {attachment.url}",
            delete_after=30,
        )

    @staticmethod
    async def _report_error(message: discord.Message, error: str):
        await message.channel.send(
            f"I could not check an image in that message: {error}", delete_after=30
        )

import io
from typing import Any, List, Optional, Tuple

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from redbot.core import commands


def _is_image_filename(filename: str) -> bool:
	lowered = filename.lower()
	return lowered.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"))


def _pick_font(image_width: int) -> Any:
	# Prefer a truetype font for cleaner rendering, but gracefully fall back.
	font_size = max(22, min(72, image_width // 12))
	for name in ("arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
		try:
			return ImageFont.truetype(name, font_size)
		except OSError:
			continue
	return ImageFont.load_default()


def _wrap_caption(draw: ImageDraw.ImageDraw, text: str, font: Any, max_width: int) -> List[str]:
	words = text.split()
	if not words:
		return [""]

	lines: List[str] = []
	current = words[0]

	for word in words[1:]:
		trial = f"{current} {word}"
		trial_width = draw.textbbox((0, 0), trial, font=font)[2]
		if trial_width <= max_width:
			current = trial
		else:
			lines.append(current)
			current = word

	lines.append(current)
	return lines


def _add_caption_banner(image: Image.Image, caption: str) -> Image.Image:
	image = image.convert("RGB")
	width, height = image.size
	side_padding = max(12, width // 32)
	top_padding = max(10, width // 50)
	line_spacing = max(4, width // 120)

	font = _pick_font(width)
	drawer = ImageDraw.Draw(image)
	lines = _wrap_caption(drawer, caption.strip(), font, width - (side_padding * 2))

	line_heights = []
	for line in lines:
		bbox = drawer.textbbox((0, 0), line, font=font)
		line_heights.append(bbox[3] - bbox[1])

	text_block_height = sum(line_heights) + line_spacing * (len(lines) - 1)
	banner_height = text_block_height + (top_padding * 2)

	final = Image.new("RGB", (width, height + banner_height), color=(255, 255, 255))
	final.paste(image, (0, banner_height))

	final_draw = ImageDraw.Draw(final)
	y = top_padding
	for idx, line in enumerate(lines):
		line_bbox = final_draw.textbbox((0, 0), line, font=font)
		line_width = line_bbox[2] - line_bbox[0]
		line_height = line_bbox[3] - line_bbox[1]
		x = (width - line_width) // 2
		final_draw.text((x, y), line, fill=(0, 0, 0), font=font)
		y += line_height + line_spacing

	return final


def _build_caption_image(raw_data: bytes, caption: str) -> Tuple[io.BytesIO, str]:
	with Image.open(io.BytesIO(raw_data)) as source:
		is_gif = source.format == "GIF"

		if is_gif:
			frames: List[Image.Image] = []
			durations: List[int] = []
			for frame in ImageSequence.Iterator(source):
				captioned = _add_caption_banner(frame, caption)
				frames.append(captioned.quantize(colors=256, method=Image.Quantize.FASTOCTREE))
				durations.append(frame.info.get("duration", source.info.get("duration", 40)))

			if frames:
				output = io.BytesIO()
				frames[0].save(
					output,
					format="GIF",
					save_all=True,
					append_images=frames[1:],
					duration=durations,
					loop=source.info.get("loop", 0),
					disposal=2,
				)
				output.seek(0)
				return output, "caption.gif"

		final = _add_caption_banner(source, caption)

	output = io.BytesIO()
	final.save(output, format="PNG")
	output.seek(0)
	return output, "caption.png"


class ImageManipulation(commands.Cog):
	"""Simple image utilities."""

	def __init__(self, bot):
		self.bot = bot
		self.session = aiohttp.ClientSession()

	def cog_unload(self):
		self.bot.loop.create_task(self.session.close())

	async def _get_image_url(self, ctx: commands.Context) -> Optional[str]:
		if ctx.message.attachments:
			for attachment in ctx.message.attachments:
				if (attachment.content_type and attachment.content_type.startswith("image/")) or _is_image_filename(attachment.filename):
					return attachment.url

		reference = ctx.message.reference
		if reference and reference.resolved and isinstance(reference.resolved, discord.Message):
			replied_message = reference.resolved
			for attachment in replied_message.attachments:
				if (attachment.content_type and attachment.content_type.startswith("image/")) or _is_image_filename(attachment.filename):
					return attachment.url

		return None

	async def _download_image(self, url: str) -> bytes:
		async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
			if resp.status != 200:
				raise RuntimeError(f"Image download failed with status {resp.status}.")

			content_type = resp.headers.get("Content-Type", "")
			if "image" not in content_type.lower():
				raise RuntimeError("That URL does not look like an image.")

			data = await resp.read()
			if len(data) > 15 * 1024 * 1024:
				raise RuntimeError("Image is too large (max 15MB).")

			return data

	@commands.command(name="caption")
	async def caption(self, ctx: commands.Context, *, text: str):
		"""Add a top caption bar to an image.

		Usage:
		- Attach an image and run `[p]caption your text`
		- Or reply to an image and run `[p]caption your text`
		"""
		caption_text = text.strip()
		if not caption_text:
			await ctx.send("Give me some caption text.")
			return

		if len(caption_text) > 180:
			await ctx.send("Keep the caption under 180 characters.")
			return

		image_url = await self._get_image_url(ctx)
		if not image_url:
			await ctx.send("Attach an image or reply to an image message, then run the command.")
			return

		try:
			async with ctx.typing():
				raw = await self._download_image(image_url)
				loop = self.bot.loop
				output, filename = await loop.run_in_executor(None, _build_caption_image, raw, caption_text)

			file = discord.File(output, filename=filename)
			await ctx.send(file=file)
		except Exception as exc:
			await ctx.send(f"Could not caption that image: {exc}")

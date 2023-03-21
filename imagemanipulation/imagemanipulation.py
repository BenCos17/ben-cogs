import discord
from discord.ext import commands
from PIL import Image, ImageFilter, ImageDraw

class ImageManipulation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def blur(self, ctx, radius: int = 5):
        """Applies a Gaussian blur to an attached image."""
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to apply the blur.")
            return

        # Download the image and apply the blur
        img = await ctx.message.attachments[0].read()
        img = Image.open(io.BytesIO(img)).convert('RGB')
        img_blur = img.filter(ImageFilter.GaussianBlur(radius=radius))

        # Save and send the blurred image
        with io.BytesIO() as img_buffer:
            img_blur.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            await ctx.send(file=discord.File(img_buffer, filename='blurred.png'))

    @commands.command()
    async def circle(self, ctx):
        """Draws a circle on an attached image."""
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to draw the circle.")
            return

        # Download the image and draw a circle
        img = await ctx.message.attachments[0].read()
        img = Image.open(io.BytesIO(img)).convert('RGBA')
        img_circle = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(img_circle)
        draw.ellipse((0, 0, img.size[0], img.size[1]), fill=(255, 255, 255, 128))
        img_circle.putalpha(128)

        # Composite the circle onto the original image and send it
        img.paste(img_circle, mask=img_circle)
        with io.BytesIO() as img_buffer:
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            await ctx.send(file=discord.File(img_buffer, filename='circled.png'))

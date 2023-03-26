import io
import discord
from redbot.core import commands
from PIL import Image, ImageFilter, ImageDraw

class ImageManipulation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

   @commands.command()
async def blur(self, ctx, radius: int = 5, user_id: int = None):
    """Applies a Gaussian blur to an attached image, a mentioned user's avatar, or a user's avatar using their ID."""
    if ctx.message.attachments:
        # Apply blur to attached image
        img = await ctx.message.attachments[0].read()
        img = Image.open(io.BytesIO(img)).convert('RGB')
    elif ctx.message.mentions:
        # Apply blur to mentioned user's avatar
        user = ctx.message.mentions[0]
        avatar_url = user.avatar_url_as(format='png', size=1024)
        img = await avatar_url.read()
        img = Image.open(io.BytesIO(img)).convert('RGB')
    elif user_id:
        # Apply blur to user's avatar using ID
        user = await self.bot.fetch_user(user_id)
        avatar_url = user.avatar_url_as(format='png', size=1024)
        img = await avatar_url.read()
        img = Image.open(io.BytesIO(img)).convert('RGB')
    else:
        await ctx.send("Please attach an image, mention a user, or provide a user ID to apply the blur.")
        return

    # Apply blur and send the result
    img_blur = img.filter(ImageFilter.GaussianBlur(radius=radius))
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

    @commands.command()
    async def grayscale(self, ctx):
        """Converts an attached image to grayscale."""
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to convert to grayscale.")
            return

        # Download the image and convert to grayscale
        img = await ctx.message.attachments[0].read()
        img = Image.open(io.BytesIO(img)).convert('L')

        # Save and send the grayscale image
        with io.BytesIO() as img_buffer:
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            await ctx.send(file=discord.File(img_buffer, filename='grayscale.png'))

    @commands.command()
    async def rotate(self, ctx):
        """Flips an attached image horizontally."""
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to flip.")
            return

        # Download the image and flip horizontally
        img = await ctx.message.attachments[0].read()
        img = Image.open(io.BytesIO(img)).transpose(Image.FLIP_LEFT_RIGHT)

        # Save and send the flipped image
        with io.BytesIO() as img_buffer:
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            await ctx.send(file=discord.File(img_buffer, filename='flipped.png'))

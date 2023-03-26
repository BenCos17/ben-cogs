import io
import discord
import typing
from redbot.core import commands
from PIL import Image, ImageFilter, ImageDraw


class ImageManipulation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def blur(self, ctx, radius: int = 5, user: typing.Union[int, discord.User] = None):
        """Applies a Gaussian blur to an attached image, a mentioned user's avatar, or a user's avatar using their ID."""
        if ctx.message.attachments or user is not None:
            # Apply blur based on the first available source (attachment or user ID/mention)
            if ctx.message.attachments:
                img = await ctx.message.attachments[0].read()
                img = Image.open(io.BytesIO(img)).convert('RGB')
            else:
                if isinstance(user, int):
                    user = await self.bot.fetch_user(user)
                avatar_url = user.avatar_url_as(format='png', size=1024)
                img = await avatar_url.read()
                img = Image.open(io.BytesIO(img)).convert('RGB')
            
            # Apply blur and send the result
            img_blur = img.filter(ImageFilter.GaussianBlur(radius=radius))
            with io.BytesIO() as img_buffer:
                img_blur.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                await ctx.send(file=discord.File(img_buffer, filename='blurred.png'))
        else:
            await ctx.send("Please attach an image, mention a user, or provide a user ID to apply the blur.")

    @commands.command()
    async def circle(self, ctx):
        """Draws a circle on an attached image."""
        if not ctx.message.attachments and not ctx.message.mentions:
            await ctx.send("Please attach an image to draw the circle.")
            return

        # Check if an image attachment was provided, otherwise try to grab the user's avatar
        if ctx.message.attachments:
            img_url = ctx.message.attachments[0].url
        else:
            user_id = ctx.message.mentions[0].id
            img_url = str(ctx.bot.get_user(user_id).avatar_url_as(format='png'))

        # Download the image and draw a circle
        img = await get_image(img_url)
        img = img.convert('RGBA')
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
async def circle(self, ctx, user: typing.Union[int, discord.User] = None):
    """Draws a circle on an attached image or a user's avatar using their ID or mention."""
    if ctx.message.attachments or user is not None:
        # Get image source based on the first available option (attachment or user ID/mention)
        if ctx.message.attachments:
            img = await get_image(ctx.message.attachments[0].url)
        else:
            if isinstance(user, int):
                user = await self.bot.fetch_user(user)
            img = await get_image(user.avatar_url_as(format='png', size=1024))
        img = img.convert('RGBA')

        # Create a transparent circle and draw it onto the image
        circle_mask = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(circle_mask)
        draw.ellipse((0, 0, img.size[0], img.size[1]), fill=(255, 255, 255, 128))
        circle_mask.putalpha(128)
        img.paste(circle_mask, mask=circle_mask)

        # Save and send the resulting image
        with io.BytesIO() as img_buffer:
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            await ctx.send(file=discord.File(img_buffer, filename='circled.png'))
    else:
        await ctx.send("Please attach an image, mention a user, or provide a user ID to draw a circle.")

@commands.command()
async def grayscale(self, ctx, user: typing.Union[int, discord.User] = None):
    """Converts an attached image or a user's avatar using their ID or mention to grayscale."""
    if ctx.message.attachments or user is not None:
        # Get image source based on the first available option (attachment or user ID/mention)
        if ctx.message.attachments:
            img = await get_image(ctx.message.attachments[0].url)
        else:
            if isinstance(user, int):
                user = await self.bot.fetch_user(user)
            img = await get_image(user.avatar_url_as(format='png', size=1024))
        img = img.convert('L')

        # Save and send the resulting image
        with io.BytesIO() as img_buffer:
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            await ctx.send(file=discord.File(img_buffer, filename='grayscale.png'))
    else:
        await ctx.send("Please attach an image, mention a user, or provide a user ID to convert to grayscale.")

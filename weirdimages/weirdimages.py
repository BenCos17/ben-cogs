import discord
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFilter
import random
import asyncio

class WeirdImages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = commands.CooldownMapping.from_cooldown(1, 15, commands.BucketType.user)

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def weird(self, ctx, size:int=500):
        """
        Generate a weird image with random shapes and filters applied
        """
        if self.cooldowns.get_bucket(ctx.message).update_rate_limit():
            return await ctx.send("You're on cooldown. Please wait before running this command again.")
        
        # create a blank image
        img = Image.new('RGB', (size, size), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        # get a drawing context
        draw = ImageDraw.Draw(img)

        # draw some random shapes
        for i in range(10):
            x1 = random.randint(0, size)
            y1 = random.randint(0, size)
            x2 = random.randint(0, size)
            y2 = random.randint(0, size)
            draw.line((x1, y1, x2, y2), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=3)
            draw.rectangle((x1, y1, x2, y2), outline=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=3)
            draw.ellipse((x1, y1, x2, y2), outline=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=3)
            draw.polygon([(x1, y1), (x2, y2), (random.randint(0, size), random.randint(0, size))], outline=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=3)

        # apply some filters
        filters = [
            ImageFilter.BLUR, 
            ImageFilter.CONTOUR, 
            ImageFilter.DETAIL, 
            ImageFilter.EDGE_ENHANCE, 
            ImageFilter.EDGE_ENHANCE_MORE, 
            ImageFilter.EMBOSS, 
            ImageFilter.FIND_EDGES, 
            ImageFilter.SHARPEN, 
            ImageFilter.SMOOTH, 
            ImageFilter.SMOOTH_MORE
        ]
        img = apply_random_filters(img, filters)

        # save the image to a file
        img.save('weird.png')

        # send the image to the chat
        await ctx.send(file=discord.File('weird.png'))

    @commands.command()
    @commands.cooldown(1

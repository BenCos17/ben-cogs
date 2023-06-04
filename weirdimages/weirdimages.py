import discord
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFilter
import random

class WeirdImages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def weird(self, ctx, size: int = 500):
        """
        Generate a weird image with random shapes and filters applied
        """
        # create a blank image
        img = Image.new('RGB', (size, size), (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        ))

        # get a drawing context
        draw = ImageDraw.Draw(img)

        # draw some random shapes
        for _ in range(10):
            x1 = random.randint(0, size)
            y1 = random.randint(0, size)
            x2 = random.randint(0, size)
            y2 = random.randint(0, size)
            draw.line((x1, y1, x2, y2), fill=self.get_random_color(), width=3)
            draw.rectangle((x1, y1, x2, y2), outline=self.get_random_color(), width=3)
            draw.ellipse((x1, y1, x2, y2), outline=self.get_random_color(), width=3)
            draw.polygon([(x1, y1), (x2, y2), (random.randint(0, size), random.randint(0, size))],
                         outline=self.get_random_color(), width=3)

        # apply some filters
        img = self.apply_random_filter(img)

        # save the image to a file
        img.save('weird.png')

        # send the image to the chat
        await ctx.send(file=discord.File('weird.png'))

    @staticmethod
    def get_random_color():
        return (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )

    @staticmethod
    def apply_random_filter(img):
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
        random_filter = random.choice(filters)
        return img.filter(random_filter)

    @commands.command()
    async def command1(self, ctx):
        # Sample functionality for command1
        author_name = ctx.author.name
        response = f"Hello {author_name}! This is command 1."
        await ctx.send(response)

    @commands.command()
    async def servername(self, ctx):
        # Sample functionality for command2
        guild_name = ctx.guild.name
        response = f"the server name is {guild_name}."
        await ctx.send(response)

# Your other existing commands can be added here as well

# End of cog class

def setup(bot):
    bot.add_cog(WeirdImages(bot))

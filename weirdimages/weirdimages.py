from redbot.core import commands
from PIL import Image, ImageDraw, ImageFilter
import random

class WeirdImages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def weird(self, ctx, size:int=500):
        """
        Generate a weird image
        """
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
        img = img.filter(ImageFilter.CONTOUR)
        img = img.filter(ImageFilter.SMOOTH_MORE)

        # save the image to a file
        img.save('weird.png')

        # send the image to the chat
        await ctx.send(file=discord.File('weird.png'))

def setup(bot):
    bot.add_cog(WeirdImages(bot))

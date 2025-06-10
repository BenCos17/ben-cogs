import discord
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import textwrap

class Clowndan(commands.Cog):
    """A cog to generate clowndan images."""

    def __init__(self, bot):
        self.bot = bot
        self.template_path = os.path.join(os.path.dirname(__file__), "clown_image_template.png")
        self.font_path = os.path.join(os.path.dirname(__file__), "font.ttf")
        self.max_text_length = 100  # Maximum characters per line

    def get_font(self, size=40):
        """Get font with fallback to default if custom font not found."""
        try:
            return ImageFont.truetype(self.font_path, size)
        except Exception:
            return ImageFont.load_default()

    def cleanup_old_images(self, save_directory):
        """Clean up images older than 1 hour."""
        import time
        current_time = time.time()
        for filename in os.listdir(save_directory):
            filepath = os.path.join(save_directory, filename)
            if os.path.getmtime(filepath) < current_time - 3600:  # 1 hour
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    @commands.command(name="memegen")
    async def clowndan(self, ctx, *, text: str):
        """Generates a clowndan image with custom text."""
        
        if not text:
            await ctx.send("Please provide text for the image.")
            return
        
        if len(text) > 200:  # Limit text length
            await ctx.send("Text is too long. Please keep it under 200 characters.")
            return

        try:
            # Load the template image
            img = Image.open(self.template_path)
            draw = ImageDraw.Draw(img)
            
            # Get font and wrap text
            font = self.get_font()
            wrapped_text = textwrap.fill(text, width=30)  # Adjust width as needed
            
            # Calculate text position for centering
            text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center the text
            x = (img.width - text_width) // 2
            y = 930  # Keep y position as is
            
            # Draw white background for text
            draw.rectangle(((0, 900), (img.width, img.height)), fill=(255, 255, 255))
            
            # Draw the text
            draw.text((x, y), wrapped_text, font=font, fill="black")

            # Save directory setup
            save_directory = os.path.join(os.path.dirname(__file__), "saved_memes")
            os.makedirs(save_directory, exist_ok=True)
            
            # Cleanup old images
            self.cleanup_old_images(save_directory)

            # Save and send
            save_path = os.path.join(save_directory, f"meme_{ctx.author.id}.png")
            img.save(save_path, format="PNG")
            
            file = discord.File(fp=save_path)
            await ctx.send(file=file)
            
            # Clean up the file after sending
            try:
                os.remove(save_path)
            except Exception:
                pass

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="memetemplate")
    async def memetemplate(self, ctx):
        """Sends the meme template without any text."""
        try:
            await ctx.send(file=discord.File(self.template_path, "template.png"))
        except Exception as e:
            await ctx.send(f"Error sending template: {str(e)}")

def setup(bot):
    bot.add_cog(Clowndan(bot))



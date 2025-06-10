import discord
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import textwrap
import logging

class Clowndan(commands.Cog):
    """A cog to generate clowndan images."""

    def __init__(self, bot):
        self.bot = bot
        self.template_path = os.path.join(os.path.dirname(__file__), "clown_image_template.png")
        self.font_path = os.path.join(os.path.dirname(__file__), "font.ttf")
        self.max_text_length = 100  # Maximum characters per line
        self.logger = logging.getLogger("red.clowndan")
        
        # Check if required files exist
        if not os.path.exists(self.template_path):
            self.logger.error(f"Template image not found at: {self.template_path}")
            raise FileNotFoundError(f"Template image not found at: {self.template_path}")
        
        self.logger.info("Clowndan cog initialized")
        self.logger.info(f"Template path: {self.template_path}")
        self.logger.info(f"Font path: {self.font_path}")

    def get_font(self, size=100):
        """Get font with fallback to default if custom font not found."""
        try:
            return ImageFont.truetype(self.font_path, size)
        except Exception as e:
            self.logger.warning(f"Failed to load custom font: {e}. Using default font.")
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
                except Exception as e:
                    self.logger.error(f"Failed to remove old image {filepath}: {e}")

    @commands.command(name="clowndan")
    async def clowndan(self, ctx, *, text: str):
        """Generates a clowndan image with custom text."""
        self.logger.info(f"clowndan command called by {ctx.author} with text: {text}")
        
        if not text:
            await ctx.send("Please provide text for the image.")
            return
        
        if len(text) > 200:  # Limit text length
            await ctx.send("Text is too long. Please keep it under 200 characters.")
            return

        try:
            # Load the template image
            self.logger.info(f"Loading template from: {self.template_path}")
            if not os.path.exists(self.template_path):
                await ctx.send("Error: Template image not found. Please contact the bot owner.")
                self.logger.error(f"Template image not found at: {self.template_path}")
                return
                
            img = Image.open(self.template_path)
            self.logger.info(f"Image size: {img.size}")
            
            draw = ImageDraw.Draw(img)
            
            # Get font and wrap text
            font = self.get_font()
            wrapped_text = textwrap.fill(text, width=15)
            
            # Calculate text position for centering
            text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            self.logger.info(f"Text size: {text_width}x{text_height}")
            
            # Center the text horizontally
            x = (img.width - text_width) // 2
            # Position the text vertically (adjust as needed)
            y = img.height - text_height - 30 # Position from the bottom, with some padding
            
            self.logger.info(f"Text position: ({x}, {y})")
            
            # Removed: Draw white background for text area
            
            # Draw the text in white color
            draw.text((x, y), wrapped_text, font=font, fill="white")

            # Save directory setup
            save_directory = os.path.join(os.path.dirname(__file__), "saved_memes")
            os.makedirs(save_directory, exist_ok=True)
            
            # Cleanup old images
            self.cleanup_old_images(save_directory)

            # Save and send
            save_path = os.path.join(save_directory, f"meme_{ctx.author.id}.png")
            self.logger.info(f"Saving image to: {save_path}")
            img.save(save_path, format="PNG")
            
            file = discord.File(fp=save_path)
            await ctx.send(file=file)
            
            # Clean up the file after sending
            try:
                os.remove(save_path)
                self.logger.info(f"Cleaned up temporary file: {save_path}")
            except Exception as e:
                self.logger.error(f"Failed to clean up temporary file {save_path}: {e}")

        except Exception as e:
            self.logger.error(f"Error in clowndan command: {e}", exc_info=True)
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    async def memetemplate(self, ctx):
        """Sends the meme template without any text."""
        try:
            if not os.path.exists(self.template_path):
                await ctx.send("Error: Template image not found. Please contact the bot owner.")
                self.logger.error(f"Template image not found at: {self.template_path}")
                return
            await ctx.send(file=discord.File(self.template_path, "template.png"))
        except Exception as e:
            self.logger.error(f"Error in memetemplate command: {e}", exc_info=True)
            await ctx.send(f"Error sending template: {str(e)}")

def setup(bot):
    bot.add_cog(Clowndan(bot))





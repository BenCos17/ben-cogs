import discord
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os  # Add this import

class Clowndan(commands.Cog):
    """A cog to generate clowndan images."""

    def __init__(self, bot):
        self.bot = bot
        # Update the template path to be relative to the current file's directory
        self.template_path = os.path.join(os.path.dirname(__file__), "clown_image_template.png")  # Adjust the filename as needed

    @commands.command(name="memegen")
    async def clowndan(self, ctx, *, text: str):
        """Generates a clowndan image with custom text."""
        
        if not text:
            await ctx.send("Please provide text for the image.")
            return
        
        # Load the template image
        try:
            img = Image.open(self.template_path)
        except Exception as e:
            await ctx.send(f"Error loading the image template: {str(e)}")
            return

        # Prepare for drawing the text
        draw = ImageDraw.Draw(img)
        
        # Use the default font provided by PIL
        font = ImageFont.load_default()  # Fallback to default font if the font file is not found

        # Position for the custom text (adjust as per the image size and template)
        text_position = (100, 930)
        
        # Draw the custom text
        draw.rectangle(((0, 900), (1024, 1024)), fill=(255, 255, 255))  # Cover old text area
        draw.text(text_position, text, font=font, fill="black")  # Add custom text

        # Define the directory to save images in the cog's path
        save_directory = os.path.join(os.path.dirname(__file__), "saved_memes")  # Create a 'saved_memes' folder in the cog directory
        os.makedirs(save_directory, exist_ok=True)  # Create the directory if it doesn't exist

        # Define the path to save the image
        save_path = os.path.join(save_directory, f"meme_{ctx.author.id}.png")  # Unique filename for each user

        # Save the image to the specified directory
        img.save(save_path, format="PNG")

        # Optionally, send the image back to the user
        file = discord.File(fp=save_path)  # Load from saved path
        await ctx.send(file=file)

    @commands.command(name="memetemplate")
    async def memetemplate(self, ctx):
        """Sends the meme template without any text (if needed)."""
        await ctx.send(file=discord.File(self.template_path, "template.png"))



def setup(bot):
    bot.add_cog(Clowndan(bot))  # Register the Clowndan cog with the bot



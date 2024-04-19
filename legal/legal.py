import discord
from rebot.core import commands
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from wand.image import Image

class LegalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="subpoena")
    async def subpoena_command(self, ctx, *, target_name: str):
        """Generate a subpoena."""
        embed = discord.Embed(
            title="SUBPOENA",
            color=0xff0000,  # Red color
            description=f"To: {target_name}\n\nYou are hereby commanded to appear before the court as a witness and to bring with you and produce the following documents: [List of documents]\n\nDate: [Date]\n\nSignature:"
        )

        await ctx.send(embed=embed)

    @commands.command(name="courtorder")
    async def court_order_command(self, ctx, target_name: str, action: str, date: str, *, signature: str):
        """Generate a court order."""
        # Generate PDF of the court order
        pdf_path = "court_order.pdf"
        self.generate_court_order_pdf(target_name, action, date, signature, pdf_path)

        # Convert PDF to image
        pdf_image_path = "court_order_preview.png"
        with Image(filename=pdf_path, resolution=300) as img:
            img.compression_quality = 99
            img.save(filename=pdf_image_path)

        # Send the PDF and the image preview in the Discord message
        with open(pdf_path, "rb") as pdf_file:
            pdf_file_data = discord.File(pdf_file, filename="court_order.pdf")
            await ctx.send(file=pdf_file_data)

        with open(pdf_image_path, "rb") as image_file:
            image_file_data = discord.File(image_file, filename="court_order_preview.png")
            await ctx.send(file=image_file_data)

    def generate_court_order_pdf(self, target_name, action, date, signature, pdf_path):
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "COURT ORDER")
        c.drawString(100, 730, f"To: {target_name}")
        c.drawString(100, 710, f"You are hereby ordered to {action}")
        c.drawString(100, 690, f"Date: {date}")
        c.drawString(100, 670, f"Signature: {signature}")
        c.save()



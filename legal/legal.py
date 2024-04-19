import discord
from redbot.core import commands
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing

class Legal(commands.Cog):
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

        # Generate thumbnail image of the first page of the PDF
        thumbnail_image = self.generate_thumbnail_image(pdf_path)

        # Send the PDF and the thumbnail image in the Discord message
        with open(pdf_path, "rb") as pdf_file:
            pdf_file_data = discord.File(pdf_file, filename="court_order.pdf")
            await ctx.send(file=pdf_file_data)

        await ctx.send(file=discord.File(thumbnail_image, filename="court_order_thumbnail.png"))

    def generate_court_order_pdf(self, target_name, action, date, signature, pdf_path):
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        content = []
        content.append(Paragraph("COURT ORDER", styles["Title"]))
        content.append(Paragraph(f"To: {target_name}", styles["Normal"]))
        content.append(Paragraph(f"You are hereby ordered to {action}", styles["Normal"]))
        content.append(Paragraph(f"Date: {date}", styles["Normal"]))
        content.append(Paragraph(f"Signature: {signature}", styles["Normal"]))
        doc.build(content)



def generate_thumbnail_image(self, pdf_path):
    thumbnail_image_path = BytesIO()

    drawing = Drawing()
    drawing.add(renderPDF.drawToFile(pdf_path, thumbnail_image_path))

    return thumbnail_image_path.getvalue()
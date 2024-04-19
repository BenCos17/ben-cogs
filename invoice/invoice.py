from redbot.core import commands
import discord
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class Invoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="invoice", aliases=["generate_invoice"])
    async def generate_invoice(self, ctx, client_name: str, amount: float):
        # Generate invoice
        invoice_number = generate_invoice_number()
        invoice_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create PDF
        pdf_filename = f"{invoice_number}.pdf"
        pdf_path = await self.create_invoice_pdf(invoice_number, invoice_date, client_name, amount, pdf_filename)

        # Send PDF as attachment
        with open(pdf_path, "rb") as file:
            invoice_pdf = discord.File(file, filename=pdf_filename)
            await ctx.send(file=invoice_pdf)

    async def create_invoice_pdf(self, invoice_number, invoice_date, client_name, amount, pdf_filename):
        # Create PDF
        pdf_path = f"/tmp/{pdf_filename}"  # Change this path to your desired location
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Invoice")
        c.drawString(100, 730, f"Invoice Number: {invoice_number}")
        c.drawString(100, 710, f"Date: {invoice_date}")
        c.drawString(100, 690, f"Client: {client_name}")
        c.drawString(100, 670, f"Amount: ${amount}")
        c.save()
        return pdf_path

def generate_invoice_number():
    # Generate a unique invoice number based on timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"INV{timestamp}"



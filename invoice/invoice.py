import os
import discord
from redbot.core import commands
import datetime
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class Invoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="invoice", aliases=["generate_invoice"])
    async def generate_invoice(self, ctx, client_name: str, amount: float, due_date: str, *items):
        try:
            # Generate invoice
            invoice_number = generate_invoice_number()
            invoice_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create PDF
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_filename = f"{invoice_number}.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)
                await self.create_invoice_pdf(invoice_number, invoice_date, client_name, amount, due_date, items, pdf_path)

                # Send PDF as attachment
                with open(pdf_path, "rb") as file:
                    invoice_pdf = discord.File(file, filename=pdf_filename)
                    await ctx.send(file=invoice_pdf)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    async def create_invoice_pdf(self, invoice_number, invoice_date, client_name, amount, due_date, items, pdf_path):
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)

        # Invoice header
        c.drawString(100, 750, "Invoice")
        c.drawString(100, 730, f"Invoice Number: {invoice_number}")
        c.drawString(100, 710, f"Date: {invoice_date}")
        c.drawString(100, 690, f"Client: {client_name}")
        c.drawString(100, 670, f"Amount: ${amount}")

        # Due date
        c.drawString(100, 650, f"Due Date: {due_date}")

        # Itemized list
        y_offset = 620
        total_amount = 0
        for item in items:
            description, quantity, unit_price = item.split(',')
            subtotal = float(quantity) * float(unit_price)
            c.drawString(100, y_offset, f"{description}: {quantity} x ${unit_price} = ${subtotal}")
            total_amount += subtotal
            y_offset -= 20

        # Total amount
        c.drawString(100, y_offset, f"Total Amount: ${total_amount}")

        c.save()

def generate_invoice_number():
    # Generate a unique invoice number based on timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"INV{timestamp}"
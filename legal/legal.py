import discord
from redbot.core import commands
import datetime  # Added for the timestamp in the court verdict embed
from PIL import Image, ImageDraw, ImageFont
import io
import os

class Legal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="subpoena")
    async def subpoena_command(self, ctx, *, target_name: str, case_number: str = "N/A", case_type: str = "N/A", court_location: str = "N/A", documents: str = "N/A", date: str = "N/A", signature: str = "N/A", title: str = "SUBPOENA", color: int = 0xff0000, footer: str = "This is an official court document.", image_template: str = "subpoena_template.png"):
        """Generate a subpoena with advanced details."""
        embed = discord.Embed(
            title=title,
            color=color,
            description=f"To: {target_name}\n\nYou are hereby commanded to appear before the court as a witness and to bring with you and produce the following documents: {documents}\n\nDate: {date}\n\nSignature: {signature}"
        )
        embed.set_footer(text=footer)
        embed.timestamp = datetime.datetime.utcnow()

        # Adding a field for case details
        embed.add_field(name="Case Details", value=f"Case Number: {case_number}\nCase Type: {case_type}\nCourt Location: {court_location}", inline=False)

        # Generate image
        image = await self.generate_image(image_template, target_name, case_number, case_type, court_location, documents, date, signature)
        await ctx.send(embed=embed, file=image)

    @commands.command(name="courtorder")
    async def court_order_command(self, ctx, target_name: str, action: str, date: str, signature: str, title: str = "COURT ORDER", color: int = 0xff0000, footer: str = "This is an official court document.", image_template: str = "court_order_template.png"):
        """Generate a court order with advanced details."""
        embed = discord.Embed(
            title=title,
            color=color,
            description=f"To: {target_name}\n\nYou are hereby ordered to {action}\n\nDate: {date}\n\nSignature: {signature}"
        )
        embed.set_footer(text=footer)
        embed.timestamp = datetime.datetime.utcnow()

        # Adding a field for case details
        embed.add_field(name="Case Details", value="Case Number: [Case Number]\nCase Type: [Case Type]\nCourt Location: [Court Location]", inline=False)

        # Generate image
        image = await self.generate_image(image_template, target_name, action, date, signature)
        await ctx.send(embed=embed, file=image)

    @commands.command(name="courtverdict")
    async def court_verdict_command(self, ctx, case_number: str, target_name: str, verdict: str, summary: str, date: str, judge_name: str, *charges: str, title: str = None, color: int = 0x0000ff, footer: str = "This is an official court document.", image_template: str = "court_verdict_template.png"):
        """Generate a detailed and realistic court verdict with advanced details."""
        # Formatting the charges for display
        formatted_charges = "\n".join([f"- {charge}" for charge in charges]) if charges else "No charges specified."

        title = title or f"Court Verdict for Case {case_number}"

        embed = discord.Embed(
            title=title,
            color=color,
            description=f"**Defendant:** {target_name}\n\n**Verdict:** {verdict}\n\n**Summary of Verdict:**\n{summary}\n\n**Charges:**\n{formatted_charges}\n\n**Date of Verdict:** {date}\n\n**Presiding Judge:** {judge_name}",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=footer)
        embed.timestamp = datetime.datetime.utcnow()

        # Adding a field for case details
        embed.add_field(name="Case Details", value="Case Number: [Case Number]\nCase Type: [Case Type]\nCourt Location: [Court Location]", inline=False)

        # Generate image
        image = await self.generate_image(image_template, case_number, target_name, verdict, summary, date, judge_name)
        await ctx.send(embed=embed, file=image)

    @commands.command(name="legalnotice")
    async def legal_notice_command(self, ctx, *, notice: str, title: str = "LEGAL NOTICE", color: int = 0xffff00, footer: str = "This is an official legal notice.", image_template: str = "legal_notice_template.png"):
        """Generate a legal notice with advanced details."""
        embed = discord.Embed(
            title=title,
            color=color,
            description=notice
        )
        embed.set_footer(text=footer)
        embed.timestamp = datetime.datetime.utcnow()

        # Adding a field for case details
        embed.add_field(name="Case Details", value="Case Number: [Case Number]\nCase Type: [Case Type]\nCourt Location: [Court Location]", inline=False)

        # Generate image
        image = await self.generate_image(image_template, notice)
        await ctx.send(embed=embed, file=image)

    @commands.command(name="warrant")
    async def warrant_command(self, ctx, target_name: str, reason: str, date: str, signature: str, title: str = "WARRANT", color: int = 0xff0000, footer: str = "This is an official warrant.", image_template: str = "warrant_template.png"):
        """Generate a warrant with advanced details."""
        embed = discord.Embed(
            title=title,
            color=color,
            description=f"To: {target_name}\n\nYou are hereby commanded to be taken into custody for the following reason: {reason}\n\nDate: {date}\n\nSignature: {signature}"
        )
        embed.set_footer(text=footer)
        embed.timestamp = datetime.datetime.utcnow()

        # Adding a field for case details
        embed.add_field(name="Case Details", value="Case Number: [Case Number]\nCase Type: [Case Type]\nCourt Location: [Court Location]", inline=False)
        # Generate image
        image = await self.generate_image(image_template, target_name, reason, date, signature)
        await ctx.send(embed=embed, file=image)

    async def generate_image(self, template, *args):
        # Load template image
        template_path = os.path.join(os.path.dirname(__file__), "templates", template)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        image = Image.open(template_path)

        # Load font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

        # Draw text on image
        draw = ImageDraw.Draw(image)
        for i, arg in enumerate(args):
            draw.text((10, 10 + i * 30), str(arg), font=font)

        # Save image to bytes
        bytes_io = io.BytesIO()
        image.save(bytes_io, format="PNG")
        bytes_io.seek(0)

        # Return image as discord.File
        return discord.File(bytes_io, "image.png")

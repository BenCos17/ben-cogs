import discord
from redbot.core import commands
import datetime  # Added for the timestamp in the court verdict embed

class Legal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="subpoena")
    async def subpoena_command(self, ctx, *, target_name: str):
        """Generate a subpoena."""
        embed = discord.Embed(
            title="SUBPOENA",
            color=0xff0000,  # Red color
            description=f"To: {target_name}\n\nYou are hereby commanded to appear before the court as a witness and to bring with you and produce the following documents: [List of documents]\n\nDate: [Date]\n\nSignature: [Your signature]"
        )

        await ctx.send(embed=embed)

    @commands.command(name="courtorder")
    async def court_order_command(self, ctx, target_name: str, action: str, date: str, signature: str):
        """Generate a court order."""
        embed = discord.Embed(
            title="COURT ORDER",
            color=0xff0000,  # Red color
            description=f"To: {target_name}\n\nYou are hereby ordered to {action}\n\nDate: {date}\n\nSignature: {signature}"
        )

        await ctx.send(embed=embed)

    @commands.command(name="courtverdict")
    async def court_verdict_command(self, ctx, case_number: str, target_name: str, verdict: str, summary: str, date: str, judge_name: str, *charges: str):
        """Generate a detailed and realistic court verdict."""
        # Formatting the charges for display
        formatted_charges = "\n".join([f"- {charge}" for charge in charges]) if charges else "No charges specified."

        embed = discord.Embed(
            title=f"Court Verdict for Case {case_number}",
            color=0x0000ff,  # Blue color
            description=f"**Defendant:** {target_name}\n\n**Verdict:** {verdict}\n\n**Summary of Verdict:**\n{summary}\n\n**Charges:**\n{formatted_charges}\n\n**Date of Verdict:** {date}\n\n**Presiding Judge:** {judge_name}",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="This is an official court document.")

        await ctx.send(embed=embed)


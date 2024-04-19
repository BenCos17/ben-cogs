import discord
from redbot.core import commands

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

def setup(bot):
    bot.add_cog(LegalCog(bot))

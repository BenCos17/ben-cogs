import discord
from redbot.core import commands

class Not(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nitro(self, ctx):
        """Generates a fake Discord Nitro link that redirects to a Rickroll."""
        fake_nitro_link = "https://discord.gift/F4k3N1tr0L1nk"  # You can customize this link if you want
        rickroll_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Link to the Rickroll video
        await ctx.send(f"Get your free Discord Nitro here: {fake_nitro_link}\nBut it's actually a Rickroll! {rickroll_link}")

def setup(bot):
    bot.add_cog(Not(bot))

from redbot.core import commands, Config
import discord

class BellCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_user = {
            "bell_count": 0
        }
        self.config.register_user(**default_user)

    @commands.command()
    async def ringbell(self, ctx):
        """Rings a bell and increases the user's bell count."""
        user = ctx.author
        bell_count = await self.config.user(user).bell_count()

        # Increment the bell count
        bell_count += 1
        await self.config.user(user).bell_count.set(bell_count)

        # Send the message with the updated bell count
        await ctx.send(f"{user.mention} rang the bell! 🔔 You have rung the bell {bell_count} times.")
        
        # Send a bell ringing gif
        gif_url = "https://github.com/BenCos17/ben-cogs/blob/main/bell/bell.gif?raw=true"
        await ctx.send(gif_url)  # Improved structure for sending the GIF

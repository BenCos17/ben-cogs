from redbot.core import commands, Config
import discord

class BellCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {
            "user_bell_counts": {}  # Changed to store user counts per guild
        }
        self.config.register_guild(**default_guild)  # Register guild-level configuration

    @commands.command()
    async def ringbell(self, ctx):
        """Rings a bell and increases the user's bell count in this server."""
        user = ctx.author  # Get the user who invoked the command
        guild = ctx.guild  # Get the guild (server) context

        # Retrieve the user bell counts for the guild
        user_bell_counts = await self.config.guild(guild).user_bell_counts()

        # Initialize and increment the user's bell count
        user_bell_counts[user.id] = user_bell_counts.get(user.id, 0) + 1
        
        # Update the counts in the config
        await self.config.guild(guild).user_bell_counts.set(user_bell_counts)

        # Send the message with the updated bell count for the user
        await ctx.send(
            f"{user.mention} rang the bell! 🔔 You have rung the bell {user_bell_counts[user.id]} times in this server."
        )

        # Send a bell ringing gif
        gif_url = "https://github.com/BenCos17/ben-cogs/blob/main/bell/bell.gif?raw=true"
        await ctx.send(gif_url)

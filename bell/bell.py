from redbot.core import commands, Config
import discord

class BellCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {
            "user_bell_counts": {}
        }
        self.config.register_guild(**default_guild)

    @commands.command()
    async def ringbell(self, ctx):
        """Rings a bell and increases the user's bell count in this server."""
        user = ctx.author
        guild = ctx.guild

        # Retrieve the user's current bell count from the config
        user_bell_count = await self.config.guild(guild).user_bell_counts.get_raw(user.id, default=0)

        # Inform the user of their previous bell count
        if user_bell_count > 0:
            await ctx.send(f"{user.mention}, you have rung the bell {user_bell_count} times before!")

        # Increment the user's bell count
        user_bell_count += 1
        
        # Update the count for this specific user in the config
        await self.config.guild(guild).user_bell_counts.set_raw(user.id, value=user_bell_count)

        # Send the message with the updated bell count for the user
        await ctx.send(
            f"{user.mention} rang the bell! 🔔 You have rung the bell {user_bell_count} times in this server."
        )

        # Send a bell ringing gif
        gif_url = "https://github.com/BenCos17/ben-cogs/blob/main/bell/bell.gif?raw=true"
        await ctx.send(gif_url)

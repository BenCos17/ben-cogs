from redbot.core import commands, Config
import discord
import asyncio
import logging

class Bell(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {
            "user_bell_counts": {}
        }
        self.config.register_guild(**default_guild)
        self.logger = logging.getLogger("red.bell")

#message method for the sent message
    async def construct_bell_message(self, user, user_bell_count: int) -> str:
        """Constructs the bell message for the user."""
        message = f"{user.mention}, "
        if user_bell_count > 0:
            message += f"you have rung the bell {user_bell_count} times before! "
        message += f"You have now rung the bell {user_bell_count + 1} times in this server. 🔔"
        return message

    async def check_guild_context(self, ctx):
        """Checks if the command is run in a guild context."""
        if ctx.guild is None:
            await ctx.send("This command cannot be used in DMs.")
            return False
        return True

#command to add another ring to the server count 
    @commands.hybrid_command(aliases=['bell'])  
    async def ringbell(self, ctx) -> None:
        """Rings a bell and increases the user's bell count in this server."""
        if not await self.check_guild_context(ctx):
            return

        user = ctx.author
        guild = ctx.guild  

        try:
            user_bell_count = await self.config.guild(guild).user_bell_counts.get_raw(user.id, default=0)
        except Exception as e:
            await ctx.send(f"An error occurred while retrieving your bell count: {str(e)}")
            return

        user_bell_count += 1  # Increment the user's bell count
        
        await self.config.guild(guild).user_bell_counts.set_raw(user.id, value=user_bell_count)

        message = await self.construct_bell_message(user, user_bell_count)

        gif_url = "https://github.com/BenCos17/ben-cogs/blob/main/bell/bell.gif?raw=true"
        await ctx.send(message + f"\n[gif]({gif_url})")  # Include the GIF URL as a clickable link

        self.logger.info(f"{user} rang the bell in {guild.name}.")



#reset a users count (only the user can run it and reset their own count)
    async def confirm_reset(self, ctx, user, user_bell_count):
        """Handles the confirmation process for resetting the bell count."""
        confirmation_message = await ctx.send(f"{user.mention}, your current bell count is {user_bell_count}. Are you sure you want to reset it to 0? (yes/no)")

        def check(m):
            return m.author == user and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            response = await self.bot.wait_for('message', check=check, timeout=30)
            if response.content.lower() == 'yes':
                await self.config.guild(ctx.guild).user_bell_counts.set_raw(user.id, value=0)
                await ctx.send(f"{user.mention}, your bell count has been reset to 0.")
                self.logger.info(f"{user} reset their bell count in {ctx.guild.name}.")
            else:
                await ctx.send(f"{user.mention}, your bell count reset has been canceled.")
        except asyncio.TimeoutError:
            await ctx.send(f"{user.mention}, you took too long to respond. The reset has been canceled.")

    @commands.command(aliases=['resetbell'])  
    async def reset_bell(self, ctx) -> None:
        """Resets the user's bell count in this server after confirmation."""
        if not await self.check_guild_context(ctx):
            return

        user = ctx.author
        guild = ctx.guild  

        try:
            user_bell_count = await self.config.guild(guild).user_bell_counts.get_raw(user.id, default=0)
        except Exception as e:
            await ctx.send(f"An error occurred while retrieving your bell count: {str(e)}")
            return

        await self.confirm_reset(ctx, user, user_bell_count)

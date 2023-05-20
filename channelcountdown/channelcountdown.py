from redbot.core import commands, Config
import discord
import asyncio
import datetime

class ChannelCountdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier for your cog
        default_config = {
            "countdowns": {}
        }
        self.config.register_guild(**default_config)
        self.rate_limit = commands.CooldownMapping.from_cooldown(2, 5.0, commands.BucketType.guild)

        self.bot.loop.create_task(self.update_channel_names())

    @commands.command()
    async def setcountdown(self, ctx, channel: discord.VoiceChannel, date: commands.clean_content):
        """
        Set a countdown for a voice channel.

        Example usage: [p]setcountdown MyChannel 31:05:2023 18:00
        """
        try:
            countdown_date = datetime.datetime.strptime(date, "%d:%m:%Y %H:%M")
        except ValueError:
            return await ctx.send("Invalid date format. Please use the format: DD:MM:YYYY HH:MM")

        guild_config = await self.config.guild(ctx.guild).countdowns()
        guild_config[channel.name] = countdown_date.strftime("%Y-%m-%d %H:%M")
        await self.config.guild(ctx.guild).countdowns.set(guild_config)
        await ctx.send(f"Countdown set for {channel.mention} to {countdown_date.strftime('%d-%m-%Y %H:%M')}")

    async def update_channel_names(self):
        # ... rest of the code

    async def rename_channel(self, channel, new_name):
        # ... rest of the code

def setup(bot):
    bot.add_cog(ChannelCountdown(bot))

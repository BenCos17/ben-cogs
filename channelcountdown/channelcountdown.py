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
    @commands.has_permissions(manage_channels=True)  # Add the necessary permission check here
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
        guild_config[channel.name] = countdown_date.strftime("%d:%m:%Y %H:%M")
        await self.config.guild(ctx.guild).countdowns.set(guild_config)
        await ctx.send(f"Countdown set for {channel.mention} to {countdown_date.strftime('%d-%m-%Y %H:%M')}")

    async def update_channel_names(self):
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                guild_config = await self.config.guild(guild).countdowns()
                for name, date_str in guild_config.items():
                    countdown_date = datetime.datetime.strptime(date_str, "%d:%m:%Y %H:%M")
                    remaining_time = countdown_date - datetime.datetime.now()

                    if remaining_time.total_seconds() <= 0:
                        continue

                    days = remaining_time.days
                    hours, remainder = divmod(remaining_time.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    countdown_name = f"Countdown: {days}d {hours}h {minutes}m"

                    for channel in guild.voice_channels:
                        if channel.name == name:
                            await self.rename_channel(channel, countdown_name)
                            break
            await asyncio.sleep(60)  # Sleep for 60 seconds before updating again

    async def rename_channel(self, channel, new_name):
        bucket = self.rate_limit.get_bucket(channel)
        if retry_after := bucket.update_rate_limit():
            await asyncio.sleep(retry_after)

        try:
            await channel.edit(name=new_name)
        except discord.HTTPException as e:
            if e.code != 50013:
                raise e

def setup(bot):
    bot.add_cog(ChannelCountdown(bot))

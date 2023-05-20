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

        self.update_channel_names.start()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_channel_names()

    @tasks.loop(seconds=60)
    async def update_channel_names(self):
        for guild in self.bot.guilds:
            guild_config = await self.config.guild(guild).countdowns()
            for name, date_str in guild_config.items():
                countdown_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
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
                else:
                    # If the voice channel doesn't exist, you can create it here if needed
                    pass

    async def rename_channel(self, channel, new_name):
        bucket = self.rate_limit.get_bucket(channel)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await asyncio.sleep(retry_after)

        try:
            await channel.edit(name=new_name)
        except discord.HTTPException as e:
            if e.code == 50013:
                # Handle "Missing Permissions" error
                pass
            else:
                raise e

    # ...

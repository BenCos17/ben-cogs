import discord
from redbot.core import commands, Config
import psutil, time

MARVEL_NAMES = [
    "IronMan", "Thor", "Hulk", "BlackWidow", "CaptainAmerica", "Loki",
    "DoctorStrange", "SpiderMan", "BlackPanther", "ScarletWitch"
]

class Clusters(commands.Cog):
    """Shows dynamic Marvel-themed cluster status with customizable names."""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(custom_names={})
        self.shard_names = {}

    async def initialize_shard_names(self):
        """Load names from config or assign defaults based on shard ID."""
        custom_names = await self.config.custom_names()
        for shard_id in self.bot.shards.keys():
            if str(shard_id) in custom_names:
                self.shard_names[shard_id] = custom_names[str(shard_id)]
            else:
                # Default persistent name
                self.shard_names[shard_id] = MARVEL_NAMES[shard_id % len(MARVEL_NAMES)]

    def uptime(self):
        seconds = int(time.time() - self.start_time)
        weeks, seconds = divmod(seconds, 604800)
        days, seconds = divmod(seconds, 86400)
        hours, _ = divmod(seconds, 3600)
        return f"{weeks} weeks and {days} days and {hours} hours ago"

    @commands.command()
    async def clusters(self, ctx):
        """Shows the status of all clusters using an embed."""
        await self.initialize_shard_names()

        embed = discord.Embed(
            title="Cluster Status",
            description=f"Bot started: {self.uptime()}",
            color=discord.Color.blue()
        )

        for shard_id, name in self.shard_names.items():
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().used / 1024**3
            latency = round(self.bot.shards[shard_id].latency * 1000)

            guilds = [g for g in self.bot.guilds if g.shard_id == shard_id]
            servers = len(guilds)
            users = sum(g.member_count or 0 for g in guilds)

            value = (
                f"**Status:** Alive Running\n"
                f"**CPU:** {cpu:.1f}%\n"
                f"**RAM:** {ram:.1f} GiB\n"
                f"**Latency:** {latency} ms\n"
                f"**Servers:** {servers}\n"
                f"**Users:** {users}\n"
                f"**Shards:** [{shard_id}]"
            )

            embed.add_field(name=f"Cluster #{name}", value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def renamecluster(self, ctx, shard_id: int, *, new_name: str):
        """Rename a cluster persistently. Owner only."""
        if shard_id not in self.bot.shards:
            await ctx.send(f"Shard ID {shard_id} does not exist.")
            return

        # Update config
        custom_names = await self.config.custom_names()
        custom_names[str(shard_id)] = new_name
        await self.config.custom_names.set(custom_names)

        # Update in-memory name
        self.shard_names[shard_id] = new_name

        await ctx.send(f"Cluster {shard_id} has been renamed to **{new_name}**.")

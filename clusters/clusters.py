import discord
from redbot.core import commands
import psutil, time, random

MARVEL_NAMES = [
    "IronMan", "Thor", "Hulk", "BlackWidow", "CaptainAmerica", "Loki",
    "DoctorStrange", "SpiderMan", "BlackPanther", "ScarletWitch"
]

class Clusters(commands.Cog):
    """Shows dynamic Marvel-themed cluster status."""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.shard_names = {}
        self._assign_shard_names()

    def _assign_shard_names(self):
        shard_ids = list(self.bot.shards.keys())
        shard_count = len(shard_ids)
        names = random.sample(MARVEL_NAMES, shard_count)
        self.shard_names = dict(zip(shard_ids, names))

    def uptime(self):
        seconds = int(time.time() - self.start_time)
        weeks, seconds = divmod(seconds, 604800)
        days, seconds = divmod(seconds, 86400)
        hours, _ = divmod(seconds, 3600)
        return f"{weeks} weeks and {days} days and {hours} hours ago"

    @commands.command()
    async def clusters(self, ctx):
        """Shows the status of all clusters using an embed."""
        embed = discord.Embed(
            title="Cluster Status",
            description=f"Bot started: {self.uptime()}",
            color=discord.Color.blue()
        )

        for shard_id, name in self.shard_names.items():
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().used / 1024**3
            latency = round(self.bot.shards[shard_id].latency * 1000)

            # Get all guilds on this shard
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

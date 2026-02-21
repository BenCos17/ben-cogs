import discord
from redbot.core import commands, Config
import psutil, datetime, json, aiohttp
from aiohttp import web

MARVEL_NAMES = [
    "IronMan", "Thor", "Hulk", "BlackWidow", "CaptainAmerica", "Loki",
    "DoctorStrange", "SpiderMan", "BlackPanther", "ScarletWitch"
]

class Clusters(commands.Cog):
    """Shows dynamic Marvel-themed cluster status with customizable names and uptime, plus a web endpoint."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(custom_names={})
        self.shard_names = {}

        # Start aiohttp web server
        self.app = web.Application()
        self.app.add_routes([web.get('/clusters', self.web_clusters)])
        self.runner = web.AppRunner(self.app)
        self.bot.loop.create_task(self.start_webserver())

    async def start_webserver(self):
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', 8080)  # Change IP/port if needed
        await self.site.start()

    async def initialize_shard_names(self):
        """Load names from config or assign defaults based on shard ID."""
        custom_names = await self.config.custom_names()
        for shard_id in self.bot.shards.keys():
            if str(shard_id) in custom_names:
                self.shard_names[shard_id] = custom_names[str(shard_id)]
            else:
                self.shard_names[shard_id] = MARVEL_NAMES[shard_id % len(MARVEL_NAMES)]

    def format_timedelta(self, td: datetime.timedelta):
        """Format a timedelta into weeks, days, hours."""
        total_seconds = int(td.total_seconds())
        weeks, remainder = divmod(total_seconds, 604800)
        days, remainder = divmod(remainder, 86400)
        hours, _ = divmod(remainder, 3600)
        return f"{weeks} weeks and {days} days and {hours} hours ago"

    def get_server_uptime(self):
        """Return server uptime as timedelta."""
        boot_timestamp = psutil.boot_time()
        return datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(boot_timestamp)

    @commands.command()
    async def clusters(self, ctx):
        """Shows the status of all clusters using an embed."""
        await self.initialize_shard_names()

        # Bot uptime (Red tracks this as bot.uptime)
        bot_start_time = getattr(self.bot, "uptime", None)
        if bot_start_time is None:
            bot_uptime_str = "Unknown"
        else:
            if isinstance(bot_start_time, datetime.datetime):
                td = datetime.datetime.utcnow() - bot_start_time
            else:
                td = bot_start_time
            bot_uptime_str = self.format_timedelta(td)

        server_uptime = self.format_timedelta(self.get_server_uptime())

        embed = discord.Embed(
            title="Cluster Status",
            description=f"**Bot uptime:** {bot_uptime_str}\n**Server uptime:** {server_uptime}",
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

        custom_names = await self.config.custom_names()
        custom_names[str(shard_id)] = new_name
        await self.config.custom_names.set(custom_names)
        self.shard_names[shard_id] = new_name

        await ctx.send(f"Cluster {shard_id} has been renamed to **{new_name}**.")

        async def web_clusters(self, request):
        """Return cluster data as JSON for web endpoint."""
        await self.initialize_shard_names()
        
        virt_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        proc = psutil.Process()
        bot_ram_gb = proc.memory_info().rss / 1024**3

        bot_start_time = getattr(self.bot, "uptime", None)
        bot_uptime_str = self.format_timedelta(datetime.datetime.utcnow() - bot_start_time) if bot_start_time else "Unknown"
        server_uptime_str = self.format_timedelta(self.get_server_uptime())

        data = {
            "bot_uptime": bot_uptime_str,
            "server_uptime": server_uptime_str,
            "system_stats": {
                "cpu_total_percent": psutil.cpu_percent(interval=None),
                "ram_used_gb": round(virt_mem.used / 1024**3, 2),
                "ram_total_gb": round(virt_mem.total / 1024**3, 2),
                "bot_ram_gb": round(bot_ram_gb, 2),
                "bot_ram_limit_gb": 10.0,
                "swap_used_gb": round(swap_mem.used / 1024**3, 2),
                "swap_total_gb": round(swap_mem.total / 1024**3, 2)
            },
            "clusters": []
        }

        for shard_id, name in self.shard_names.items():
            guilds = [g for g in self.bot.guilds if g.shard_id == shard_id]
            data["clusters"].append({
                "shard_id": shard_id,
                "name": name,
                "servers": len(guilds),
                "users": sum(g.member_count or 0 for g in guilds),
                "latency_ms": round(self.bot.shards[shard_id].latency * 1000)
            })

        return web.json_response(data)


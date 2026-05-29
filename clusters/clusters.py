import discord
from redbot.core import commands, Config
import psutil, datetime, json, aiohttp
from aiohttp import web
import platform
import os
from pathlib import Path

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

    def get_system_snapshot(self):
        """Return a reusable snapshot of host and process stats."""
        virt_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        proc = psutil.Process()
        cpu_count_logical = psutil.cpu_count(logical=True) or os.cpu_count()
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_count_affinity = None
        try:
            cpu_count_affinity = len(proc.cpu_affinity())
        except (AttributeError, NotImplementedError, psutil.Error):
            cpu_count_affinity = None

        cpu_count_display = cpu_count_physical or cpu_count_affinity or cpu_count_logical
        disk_root = Path.cwd().anchor or Path.cwd().drive or "/"

        try:
            disk_usage = psutil.disk_usage(disk_root)
        except Exception:
            disk_usage = None

        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "Unknown",
            "python_version": platform.python_version(),
            "cpu_logical": cpu_count_logical,
            "cpu_physical": cpu_count_physical,
            "cpu_count": cpu_count_display,
            "cpu_affinity": cpu_count_affinity,
            "cpu_usage_percent": psutil.cpu_percent(interval=None),
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None,
            "ram_used_gb": round(virt_mem.used / 1024**3, 2),
            "ram_total_gb": round(virt_mem.total / 1024**3, 2),
            "ram_percent": virt_mem.percent,
            "swap_used_gb": round(swap_mem.used / 1024**3, 2),
            "swap_total_gb": round(swap_mem.total / 1024**3, 2),
            "swap_percent": swap_mem.percent,
            "disk_used_gb": round(disk_usage.used / 1024**3, 2) if disk_usage else None,
            "disk_total_gb": round(disk_usage.total / 1024**3, 2) if disk_usage else None,
            "disk_percent": disk_usage.percent if disk_usage else None,
            "process_rss_gb": round(proc.memory_info().rss / 1024**3, 2),
            "process_cpu_percent": proc.cpu_percent(interval=None),
            "process_threads": proc.num_threads(),
            "process_open_files": None,
        }

    @commands.command()
    async def clusters(self, ctx):
        """Shows the status of all clusters using an embed."""
        await self.initialize_shard_names()

        bot_start_time = getattr(self.bot, "uptime", None)
        if bot_start_time is None:
            bot_uptime_str = "Unknown"
        else:
            td = datetime.datetime.utcnow() - bot_start_time if isinstance(bot_start_time, datetime.datetime) else bot_start_time
            bot_uptime_str = self.format_timedelta(td)

        server_uptime = self.format_timedelta(self.get_server_uptime())
        system = self.get_system_snapshot()

        embed = discord.Embed(
            title="Cluster Status",
            description=f"**Bot uptime:** {bot_uptime_str}\n**Server uptime:** {server_uptime}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="System",
            value=(
                f"**OS:** {system['platform']}\n"
                f"**CPU:** {system['cpu_usage_percent']}% ({system['cpu_count']} cores"
                + (
                    f", {system['cpu_physical']} physical / {system['cpu_logical']} logical"
                    if system['cpu_physical'] is not None and system['cpu_logical'] is not None
                    else ""
                )
                + ")\n"
                f"**RAM:** {system['ram_used_gb']} / {system['ram_total_gb']} GB ({system['ram_percent']}%)\n"
                f"**Swap:** {system['swap_used_gb']} / {system['swap_total_gb']} GB ({system['swap_percent']}%)"
            ),
            inline=False,
        )

        if system["disk_used_gb"] is not None:
            embed.add_field(
                name="Storage",
                value=(
                    f"**Root:** {system['disk_used_gb']} / {system['disk_total_gb']} GB ({system['disk_percent']}%)\n"
                    f"**Python:** {system['python_version']}"
                ),
                inline=False,
            )

        embed.add_field(
            name="Process",
            value=(
                f"**Bot RAM:** {system['process_rss_gb']} GB\n"
                f"**Bot CPU:** {system['process_cpu_percent']}%\n"
                f"**Threads:** {system['process_threads']}"
            ),
            inline=False,
        )

        for shard_id, name in self.shard_names.items():
            latency = round(self.bot.shards[shard_id].latency * 1000)
            guilds = [g for g in self.bot.guilds if g.shard_id == shard_id]
            
            value = (
                f"**Status:** Alive Running\n"
                f"**Latency:** {latency} ms\n"
                f"**Servers:** {len(guilds)}\n"
                f"**Users:** {sum(g.member_count or 0 for g in guilds)}\n"
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

        system = self.get_system_snapshot()

        bot_start_time = getattr(self.bot, "uptime", None)
        bot_uptime_str = self.format_timedelta(datetime.datetime.utcnow() - bot_start_time) if bot_start_time else "Unknown"
        server_uptime_str = self.format_timedelta(self.get_server_uptime())

        data = {
            "bot_uptime": bot_uptime_str,
            "server_uptime": server_uptime_str,
            "system_stats": {
                **system,
                "cpu_total_percent": system["cpu_usage_percent"],
                "bot_ram_gb": system["process_rss_gb"],
                "bot_ram_limit_gb": 10.0,
            },
            "clusters": []
        }

        # Use the bot's reported shard count
        total_shards = self.bot.shard_count or 1
        for shard_id in range(total_shards):
            # 1. Get name safely
            name = self.shard_names.get(shard_id, MARVEL_NAMES[shard_id % len(MARVEL_NAMES)])
            
            # 2. Get shard object safely
            shard = self.bot.get_shard(shard_id)
            
            # 3. Determine status and latency
            # We explicitly check shard health to provide the 'status' key
            is_online = shard is not None and not shard.is_closed()
            latency = round(shard.latency * 1000) if (is_online and shard.latency is not None) else 0
            
            # 4. Count guilds on this shard
            guilds = [g for g in self.bot.guilds if g.shard_id == shard_id]
            
            data["clusters"].append({
                "shard_id": shard_id,
                "name": name,
                "servers": len(guilds),
                "users": sum(g.member_count or 0 for g in guilds),
                "latency_ms": latency,
                "status": "Online" if is_online else "Offline"
            })

        return web.json_response(data)
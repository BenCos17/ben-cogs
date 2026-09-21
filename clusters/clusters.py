import discord
from redbot.core import commands, Config
import psutil, datetime, json, aiohttp
from aiohttp import web
import asyncio
import platform
import os
from pathlib import Path
from collections import deque

MARVEL_NAMES = [
    "IronMan", "Thor", "Hulk", "BlackWidow", "CaptainAmerica", "Loki",
    "DoctorStrange", "SpiderMan", "BlackPanther", "ScarletWitch"
]

COG_VERSION = "1.0.1"
UPTIME_SAMPLE_INTERVAL = 60
UPTIME_HISTORY_LIMIT = 1440

class Clusters(commands.Cog):
    """Shows dynamic Marvel-themed cluster status with customizable names and uptime, plus a web endpoint."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(custom_names={})
        self.shard_names = {}
        self.runner = None
        self.site = None
        self.uptime_history = deque(maxlen=UPTIME_HISTORY_LIMIT)
        self.uptime_task = self.bot.loop.create_task(self.collect_uptime())

        # Start aiohttp web server
        self.app = web.Application()
        self.app.add_routes([
            web.get('/clusters', self.web_clusters),
            web.get('/clusters/dashboard', self.web_dashboard),
        ])
        self.runner = web.AppRunner(self.app)
        self.bot.loop.create_task(self.start_webserver())

    async def start_webserver(self):
        if self.runner is None:
            self.runner = web.AppRunner(self.app)

        await self.runner.setup()

        last_error = None
        for _ in range(10):
            try:
                self.site = web.TCPSite(self.runner, '0.0.0.0', 8080)  # Change IP/port if needed
                await self.site.start()
                return
            except OSError as error:
                last_error = error
                if error.errno != 98:
                    raise
                await asyncio.sleep(0.5)

        if last_error is not None:
            raise last_error

        raise RuntimeError("Failed to start the clusters webserver for an unknown reason.")

    async def shutdown_webserver(self):
        if self.uptime_task is not None:
            self.uptime_task.cancel()
            self.uptime_task = None

        if self.site is not None:
            await self.site.stop()
            self.site = None

        if self.runner is not None:
            await self.runner.cleanup()
            self.runner = None

    def cog_unload(self):
        if self.bot and self.bot.loop.is_running():
            self.bot.loop.create_task(self.shutdown_webserver())

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

    def get_bot_uptime(self):
        """Return bot uptime as a timedelta when Red provides it."""
        bot_start_time = getattr(self.bot, "uptime", None)
        if bot_start_time is None:
            return None
        if isinstance(bot_start_time, datetime.timedelta):
            return bot_start_time
        if isinstance(bot_start_time, datetime.datetime):
            return datetime.datetime.utcnow() - bot_start_time
        return None

    async def collect_uptime(self):
        """Keep a bounded history for the uptime graph."""
        try:
            while True:
                bot_uptime = self.get_bot_uptime()
                self.uptime_history.append({
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp(),
                    "bot_uptime_seconds": round(bot_uptime.total_seconds(), 1) if bot_uptime else None,
                    "server_uptime_seconds": round(self.get_server_uptime().total_seconds(), 1),
                })
                await asyncio.sleep(UPTIME_SAMPLE_INTERVAL)
        except asyncio.CancelledError:
            raise

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

        bot_uptime = self.get_bot_uptime()
        if bot_uptime is None:
            bot_uptime_str = "Unknown"
        else:
            bot_uptime_str = self.format_timedelta(bot_uptime)

        server_uptime = self.format_timedelta(self.get_server_uptime())
        system = self.get_system_snapshot()

        description = (
            f"**Bot uptime:** {bot_uptime_str}\n"
            f"**Server uptime:** {server_uptime}"
        )
        if ctx.guild is not None:
            shard_id = ctx.guild.shard_id
            cluster_name = self.shard_names.get(
                shard_id, MARVEL_NAMES[shard_id % len(MARVEL_NAMES)]
            )
            description += f"\n**This server:** Cluster #{cluster_name} (shard {shard_id})"

        embed = discord.Embed(
            title="Cluster Status",
            description=description,
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


    async def get_web_data(self):
        """Build the shared payload used by the API and dashboard."""
        await self.initialize_shard_names()

        system = self.get_system_snapshot()

        bot_uptime = self.get_bot_uptime()
        bot_uptime_str = self.format_timedelta(bot_uptime) if bot_uptime else "Unknown"
        server_uptime_str = self.format_timedelta(self.get_server_uptime())

        data = {
            "version": COG_VERSION,
            "bot_uptime": bot_uptime_str,
            "server_uptime": server_uptime_str,
            "uptime_history": list(self.uptime_history),
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

        return data

    async def web_clusters(self, request):
        """Return cluster data as JSON for web endpoint."""
        return web.json_response(await self.get_web_data())

    async def web_dashboard(self, request):
        """Return a standalone dashboard without requiring API calls from the client."""
        data = await self.get_web_data()
        data_json = json.dumps(data).replace("<", "\\u003c")
        return web.Response(text=f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60"><title>Cluster Dashboard</title>
<style>
body{{font:16px system-ui,sans-serif;margin:0;padding:2rem;background:#101827;color:#e5e7eb}}
main{{max-width:1100px;margin:auto}} h1{{margin-top:0}} .summary{{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0 1.5rem}}
.card{{background:#182235;border:1px solid #334155;padding:1rem;min-width:180px}} .label{{color:#94a3b8;font-size:.85rem}}
.clusters{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin-bottom:1.5rem}}
.online{{color:#4ade80}} .offline{{color:#f87171}} canvas{{width:100%;height:360px;background:#182235;border:1px solid #334155}}
</style></head><body><main><h1>Cluster Dashboard</h1>
<div class="summary" id="summary"></div><div class="clusters" id="clusters"></div>
<canvas id="chart" width="1100" height="360"></canvas></main>
<script id="dashboard-data" type="application/json">{data_json}</script>
<script>
const data = JSON.parse(document.getElementById('dashboard-data').textContent);
const formatUptime = value => value == null ? 'Unknown' : value;
document.getElementById('summary').innerHTML = [
    ['Bot uptime', formatUptime(data.bot_uptime)], ['Server uptime', data.server_uptime],
    ['Clusters', data.clusters.length], ['Version', data.version]
].map(([label, value]) => `<div class="card"><div class="label">${{label}}</div><strong>${{value}}</strong></div>`).join('');
document.getElementById('clusters').innerHTML = data.clusters.map(cluster =>
    `<div class="card"><strong>${{cluster.name}}</strong><div class="${{cluster.status.toLowerCase()}}">${{cluster.status}}</div><div>${{cluster.servers}} servers, ${{cluster.users}} users</div><div>${{cluster.latency_ms}} ms latency</div></div>`).join('');
const samples = data.uptime_history, canvas = document.getElementById('chart'), ctx = canvas.getContext('2d');
const width = canvas.width, height = canvas.height, padding = 45;
const values = samples.flatMap(sample => [sample.bot_uptime_seconds, sample.server_uptime_seconds].filter(Number.isFinite));
if (values.length) {{
    const max = Math.max(...values, 1), x = index => padding + index * (width - padding * 2) / Math.max(samples.length - 1, 1);
    const y = value => height - padding - value * (height - padding * 2) / max;
    ctx.strokeStyle = '#475569'; ctx.beginPath(); ctx.moveTo(padding, padding); ctx.lineTo(padding, height - padding); ctx.lineTo(width - padding, height - padding); ctx.stroke();
    [['server_uptime_seconds','#38bdf8'],['bot_uptime_seconds','#fbbf24']].forEach(([key, color]) => {{
        ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.beginPath();
        samples.forEach((sample, index) => {{ if (!Number.isFinite(sample[key])) return; const point = [x(index), y(sample[key])]; index ? ctx.lineTo(...point) : ctx.moveTo(...point); }}); ctx.stroke();
    }});
    ctx.fillStyle = '#38bdf8'; ctx.fillText('Server', padding, 20); ctx.fillStyle = '#fbbf24'; ctx.fillText('Bot', padding + 70, 20);
}}
</script></body></html>""", content_type="text/html")
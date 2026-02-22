import discord
import json
import logging
import datetime
import time
from pathlib import Path
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription

log = logging.getLogger("red.iss")

class ISS(commands.Cog):
    """J.A.R.V.I.S. ISS Command Center - Final Build"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        self.last_update = None
        self.last_item_update = {}
        
        cog_path = Path(__file__).parent
        with open(cog_path / "telemetry.json", "r") as f:
            self.telemetry_map = json.load(f)

        self.all_ids = []
        for category in self.telemetry_map.values():
            self.all_ids.extend(category.keys())
            
        self.data_cache = {k: "Connecting..." for k in self.all_ids}
        self.start_ls_client()

    def start_ls_client(self):
        try:
            self.ls_client = LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE")
            sub = Subscription(mode="MERGE", items=self.all_ids, fields=["Value"])
            
            class LSListener:
                def __init__(self, outer): 
                    self.outer = outer

                def onItemUpdate(self, update):
                    item = update.getItemName()
                    val = update.getValue("Value")
                    now = time.time()
                    
                    self.outer.last_update = datetime.datetime.fromtimestamp(now, datetime.timezone.utc)
                    self.outer.last_item_update[item] = now 
                    
                    if val is None:
                        return

                    try:
                        num = float(val)
                        # Smart Units & Precision
                        if "Voltage" in item: self.outer.data_cache[item] = f"{num:.3f}"
                        elif "Angle" in item or item.endswith(("PIT", "YAW", "ROL")): self.outer.data_cache[item] = f"{num:.2f}"
                        elif "Mass" in item: self.outer.data_cache[item] = f"{num:,.0f}"
                        else: self.outer.data_cache[item] = f"{num:,.2f}"
                    except (ValueError, TypeError):
                        self.outer.data_cache[item] = str(val)

            sub.addListener(LSListener(self))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
        except Exception as e:
            log.error(f"ISS Mimic Connection Failure: {e}")

    def cog_unload(self):
        if self.ls_client: 
            self.ls_client.disconnect()

    async def build_embed(self, category_keys: list, title: str, color: int):
        embed = discord.Embed(title=title, color=color)
        now = time.time()
        
        for key in category_keys:
            sensors = self.telemetry_map.get(key, {})
            lines = []
            active_in_cat = False
            
            for id_k, label in sensors.items():
                val = self.data_cache.get(id_k, "Connecting...")
                # Mark active sensors with a small dot
                is_active = (now - self.last_item_update.get(id_k, 0)) < 60
                prefix = "🔹 " if is_active else ""
                lines.append(f"{prefix}**{label}:** `{val}`")
                if is_active: active_in_cat = True

            status_emoji = "🟢" if active_in_cat else "💤"
            embed.add_field(name=f"{status_emoji} {key.replace('_', ' ')}", value="\n".join(lines), inline=True)
        
        if self.last_update:
            ts = self.last_update.strftime("%H:%M:%S UTC")
            embed.set_footer(text=f"NASA Stream: {ts} | Signal: Acquired 📡")
        return embed

    @commands.group(invoke_without_command=True)
    async def iss(self, ctx):
        """ISS Telemetry Command Hub"""
        await ctx.send_help()

    @iss.command(name="all")
    async def iss_all(self, ctx):
        """Station Overview (Dual-Module Feed)"""
        e1 = await self.build_embed(["GNC", "ETHOS_AIR", "ETHOS_WATER"], "🛰️ Primary Systems", 0x2b2d31)
        e2 = await self.build_embed(["SPARTAN_POWER", "ROBOTICS", "RUSSIAN"], "🛰️ Engineering & Logistics", 0x2b2d31)
        await ctx.send(embed=e1)
        await ctx.send(embed=e2)

    @iss.command(name="status")
    async def iss_status(self, ctx):
        """Sensor Activity Report"""
        now = time.time()
        active = [id_k for id_k in self.all_ids if (now - self.last_item_update.get(id_k, 0)) < 60]
        
        embed = discord.Embed(title="📡 Data Stream Health", color=0x2ecc71 if active else 0xe74c3c)
        embed.add_field(name="Summary", value=f"✅ Active: `{len(active)}` | 💤 Standby: `{len(self.all_ids)-len(active)}`", inline=False)
        
        if active:
            # Get first 15 names
            names = []
            for id_k in active[:15]:
                for cat in self.telemetry_map.values():
                    if id_k in cat: names.append(f"🟢 {cat[id_k]}")
            embed.description = "**Currently Streaming:**\n" + "\n".join(names)
        else:
            embed.description = "⚠️ No active data. Station may be in LOS (Loss of Signal)."
            
        await ctx.send(embed=embed)


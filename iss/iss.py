import discord
import json
import logging
import datetime
import time
import asyncio
import math
from pathlib import Path
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from lightstreamer.client import LightstreamerClient, Subscription

log = logging.getLogger("red.iss")

class CategorySelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label="Primary GNC", value="GNC", description="Altitude, Velocity, Attitude", emoji="🚀"),
            discord.SelectOption(label="Air Systems", value="ETHOS_AIR", description="Pressure, Temp, CO2", emoji="🌬️"),
            discord.SelectOption(label="Water Systems", value="ETHOS_WATER", description="Urine Tank, Clean Water", emoji="💧"),
            discord.SelectOption(label="Power Status", value="SPARTAN_POWER", description="Solar Arrays & SARJ", emoji="⚡"),
            discord.SelectOption(label="Robotics", value="ROBOTICS", description="Canadarm2 Joint Data", emoji="🦾"),
            discord.SelectOption(label="EVA Suits", value="EVA_SUITS", description="Suit Voltages & Pressure", emoji="👨‍🚀"),
            discord.SelectOption(label="EVA Power", value="EVA_POWER", description="Airlock & IRU Power", emoji="🔋"),
            discord.SelectOption(label="Russian Segment", value="RUSSIAN", description="Docking & RS Mode", emoji="🇷🇺"),
=            discord.SelectOption(label="Communications", value="COMMUNICATIONS", description="Radios & Antennas", emoji="📡"),
            discord.SelectOption(label="Rendezvous", value="RENDEZVOUS", description="Approach Monitor", emoji="🛰️"),
        
        ]
        super().__init__(placeholder="Select a system to monitor...", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = await self.cog.build_embed([self.values[0]], f"🛰️ {self.values[0]} Telemetry", 0x2b2d31)
        await interaction.response.send_message(embed=embed, ephemeral=False)

class SelectionView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.add_item(CategorySelect(cog))

class ISS(commands.Cog):
    """J.A.R.V.I.S. ISS Command Center - Interactive Build"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        self.last_update = None
        self.last_item_update = {}
        self.discovered_ids = set()
        
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
                    
                    if val is None: return
                    try:
                        num = float(val)
                        if item in ["USLAB000001", "USLAB000002", "USLAB000003", "USLAB000004"]:
                            self.outer.data_cache[item] = "Active ✅" if int(num) == 1 else "Standby 💤"
                        elif "Voltage" in item: self.outer.data_cache[item] = f"{num:.2f} V"
                        elif "Current" in item: self.outer.data_cache[item] = f"{num:.2f} A"
                        elif "Angle" in item or item.endswith(("PIT", "YAW", "ROL")): self.outer.data_cache[item] = f"{num:.2f}°"
                        elif "Mass" in item: self.outer.data_cache[item] = f"{num:,.0f} kg"
                        elif "ALT" in item: self.outer.data_cache[item] = f"{num:.2f} km"
                        else: self.outer.data_cache[item] = f"{num:,.2f}"
                    except (ValueError, TypeError):
                        self.outer.data_cache[item] = str(val)

            sub.addListener(LSListener(self))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
        except Exception as e:
            log.error(f"failed to connect to ISS telemetry: {e}")

    def cog_unload(self):
        if self.ls_client: self.ls_client.disconnect()

    async def build_embed(self, category_keys: list, title: str, color: int):
        embed = discord.Embed(title=title, color=color)
        now = time.time()
        
        if "GNC" in category_keys:
            try:
                vx = float(self.data_cache.get("USLAB000035", "0").split()[0].replace(",", ""))
                vy = float(self.data_cache.get("USLAB000036", "0").split()[0].replace(",", ""))
                vz = float(self.data_cache.get("USLAB000037", "0").split()[0].replace(",", ""))
                total_v = math.sqrt(vx**2 + vy**2 + vz**2)
                embed.description = f"🚀 **Total Orbital Velocity:** `{total_v:,.2f} m/s`"
            except:
                embed.description = "🚀 **Total Orbital Velocity:** `Calculating...`"

        for key in category_keys:
            sensors = self.telemetry_map.get(key, {})
            lines = []
            active_in_cat = False
            for id_k, label in sensors.items():
                val = self.data_cache.get(id_k, "Connecting...")
                is_active = (now - self.last_item_update.get(id_k, 0)) < 60
                if is_active: active_in_cat = True
                prefix = "🔹 " if is_active else "🔸 "
                lines.append(f"{prefix}**{label}:** `{val}`")
            
            status_emoji = "🟢" if active_in_cat else "💤"
            embed.add_field(name=f"{status_emoji} {key.replace('_', ' ')}", value="\n".join(lines) or "No Data", inline=True)
        
        if self.last_update:
            embed.set_footer(text=f"NASA Live: {self.last_update.strftime('%H:%M:%S UTC')} | Signal: Acquired 📡")
        return embed

    @commands.group(invoke_without_command=True)
    async def iss(self, ctx):
        """ISS Telemetry Command Hub"""
        view = SelectionView(self)
        await ctx.send("📡 **Mission Control Console**\nSelect a system to view live station telemetry:", view=view)

    @iss.command(name="all")
    async def iss_all(self, ctx):
        """Station Overview (Dual-Module Feed)"""
        e1 = await self.build_embed(["GNC", "ETHOS_AIR", "ETHOS_WATER"], "🛰️ Primary Systems", 0x2b2d31)
        e2 = await self.build_embed(["SPARTAN_POWER", "ROBOTICS", "EVA_POWER", "RUSSIAN"], "🛰️ Engineering & Logistics", 0x2b2d31)
        await ctx.send(embed=e1)
        await ctx.send(embed=e2)

    @iss.command(name="gnc")
    async def iss_gnc(self, ctx):
        """Guidance, Navigation, and Control"""
        embed = await self.build_embed(["GNC"], "🚀 Orbital GNC Status", 0x2ecc71)
        await ctx.send(embed=embed)

    @iss.command(name="ethos")
    async def iss_ethos(self, ctx):
        """Environment & Life Support"""
        embed = await self.build_embed(["ETHOS_AIR", "ETHOS_WATER"], "🌡️ Life Support Systems", 0x3498db)
        await ctx.send(embed=embed)

    @iss.command(name="comm")
    async def iss_comm(self, ctx):
        await ctx.send(embed=await self.build_embed(["COMMUNICATIONS"], "📡 Station Comms", 0x607d8b))

    @iss.command(name="approach")
    async def iss_approach(self, ctx):
        await ctx.send(embed=await self.build_embed(["RENDEZVOUS"], "🛰️ Rendezvous Monitor", 0xe91e63))

    @iss.command(name="robotics")
    async def iss_robotics(self, ctx):
        """Canadarm2 Status"""
        embed = await self.build_embed(["ROBOTICS"], "🦾 SSRMS Robotics", 0xe67e22)
        await ctx.send(embed=embed)

    @iss.command(name="eva")
    async def iss_eva(self, ctx):
        """Extravehicular Activity & Airlock"""
        embed = await self.build_embed(["EVA_SUITS", "EVA_POWER"], "👨‍🚀 EVA Operations", 0x9b59b6)
        await ctx.send(embed=embed)

    @iss.command(name="status")
    async def iss_status(self, ctx):
        """Sensor Activity Report"""
        now = time.time()
        active = [id_k for id_k in self.all_ids if (now - self.last_item_update.get(id_k, 0)) < 60]
        embed = discord.Embed(title="📡 Stream Health", color=0x2ecc71 if active else 0xe74c3c)
        embed.add_field(name="Data Points", value=f"✅ Active: `{len(active)}` | 💤 Standby: `{len(self.all_ids)-len(active)}`", inline=False)
        await ctx.send(embed=embed)

    @iss.command(name="reconnect")
    @commands.is_owner()
    async def iss_reconnect(self, ctx):
        """Restart the NASA link (Owner Only)"""
        await ctx.send("🔄 Resetting telemetry link...")
        if self.ls_client: self.ls_client.disconnect()
        self.start_ls_client()
        await ctx.send("✅ Connection re-established.")

    @iss.command(name="scan")
    @commands.is_owner()
    async def iss_scan(self, ctx):
        """Hunt for untracked NASA Opcodes (Owner Only)"""
        await ctx.send("🛰️ **Scanning broad-range telemetry...** (30s)")
        prefixes = ["USLAB", "NODE1", "NODE2", "NODE3", "AIRLOCK", "SSRMS", "S1", "P1"]
        test_ids = [f"{p}{str(i).zfill(7)}" for p in prefixes for i in range(1, 20)]
        scan_sub = Subscription(mode="MERGE", items=test_ids, fields=["Value"])
        self.ls_client.subscribe(scan_sub)
        await asyncio.sleep(30)
        self.ls_client.unsubscribe(scan_sub)
        await ctx.send(f"✅ Scan complete. Found `{len(self.discovered_ids)}` new Opcodes.")

    @iss.command(name="discover")
    @commands.is_owner()
    async def iss_discover(self, ctx):
        """Show untracked IDs caught by the scanner (Owner Only)"""
        if not self.discovered_ids: return await ctx.send("❌ No IDs detected.")
        pages = [box(p, lang="text") for p in pagify("\n".join(sorted(list(self.discovered_ids))), page_length=1000)]
        await menu(ctx, pages, DEFAULT_CONTROLS)
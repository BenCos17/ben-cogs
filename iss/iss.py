import discord
import json
import logging
import datetime
import time
from pathlib import Path
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription

log = logging.getLogger("red.iss")

# --- UI Components for Choosing Categories ---

class CategorySelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        # These values must match the keys in your telemetry.json exactly
        options = [
            discord.SelectOption(label="Primary GNC", value="GNC", description="Altitude, Velocity, Attitude", emoji="🚀"),
            discord.SelectOption(label="Air Systems", value="ETHOS_AIR", description="Pressure, Temp, CO2", emoji="🌬️"),
            discord.SelectOption(label="Water Systems", value="ETHOS_WATER", description="Urine Tank, Clean Water", emoji="💧"),
            discord.SelectOption(label="Power Status", value="SPARTAN_POWER", description="Solar Arrays & SARJ", emoji="⚡"),
            discord.SelectOption(label="Robotics", value="ROBOTICS", description="Canadarm2 Joint Data", emoji="🦾"),
            discord.SelectOption(label="EVA / Airlock", value="EVA_SUITS", description="Suit Voltages & Pressure", emoji="👨‍🚀"),
            discord.SelectOption(label="Russian Segment", value="RUSSIAN", description="Docking & RS Mode", emoji="🇷🇺"),
        ]
        super().__init__(placeholder="Select a system to monitor...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # build_embed expects a list of keys
        embed = await self.cog.build_embed([self.values[0]], f"🛰️ {self.values[0]} Telemetry", 0x2b2d31)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class SelectionView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.add_item(CategorySelect(cog))

# --- Main Cog ---

class ISS(commands.Cog):
    """J.A.R.V.I.S. ISS Command Center - Interactive Build"""

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
                    
                    if val is None: return
                    try:
                        num = float(val)
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
        if self.ls_client: self.ls_client.disconnect()

    async def build_embed(self, category_keys: list, title: str, color: int):
        embed = discord.Embed(title=title, color=color)
        now = time.time()
        for key in category_keys:
            sensors = self.telemetry_map.get(key, {})
            lines = []
            active_in_cat = False
            for id_k, label in sensors.items():
                val = self.data_cache.get(id_k, "Connecting...")
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
        # This now sends the interactive "Choice" menu
        view = SelectionView(self)
        await ctx.send("📡 **Interactive ISS Telemetry Console**\nChoose a category below to view live data:", view=view)

    @iss.command(name="all")
    async def iss_all(self, ctx):
        """Station Overview (Dual-Module Feed)"""
        e1 = await self.build_embed(["GNC", "ETHOS_AIR", "ETHOS_WATER"], "🛰️ Primary Systems", 0x2b2d31)
        e2 = await self.build_embed(["SPARTAN_POWER", "ROBOTICS", "RUSSIAN"], "🛰️ Engineering & Logistics", 0x2b2d31)
        await ctx.send(embed=e1)
        await ctx.send(embed=e2)

    # --- Added Individual Category Commands ---

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

    @iss.command(name="robotics")
    async def iss_robotics(self, ctx):
        """Canadarm2 Status"""
        embed = await self.build_embed(["ROBOTICS"], "🦾 SSRMS Robotics", 0xe67e22)
        await ctx.send(embed=embed)

    @iss.command(name="status")
    async def iss_status(self, ctx):
        """Sensor Activity Report"""
        now = time.time()
        active = [id_k for id_k in self.all_ids if (now - self.last_item_update.get(id_k, 0)) < 60]
        embed = discord.Embed(title="📡 Data Stream Health", color=0x2ecc71 if active else 0xe74c3c)
        embed.add_field(name="Summary", value=f"✅ Active: `{len(active)}` | 💤 Standby: `{len(self.all_ids)-len(active)}`", inline=False)
        if active:
            names = []
            for id_k in active[:15]:
                for cat in self.telemetry_map.values():
                    if id_k in cat: names.append(f"🟢 {cat[id_k]}")
            embed.description = "**Currently Streaming:**\n" + "\n".join(names)
        else:
            embed.description = "⚠️ No active data. Station may be in LOS (Loss of Signal)."
        await ctx.send(embed=embed)
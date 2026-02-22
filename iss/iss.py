import discord
import json
import logging
import datetime
from pathlib import Path
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription

log = logging.getLogger("red.iss")

class ISS(commands.Cog):
    """The Maximum Detail ISS-Mimic Suite"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        self.last_update = None
        
        # Load the expanded telemetry mapping
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
                def __init__(self, outer): self.outer = outer
                def onItemUpdate(self, update):
                    item, val = update.getItemName(), update.getValue("Value")
                    self.outer.last_update = datetime.datetime.now(datetime.timezone.utc)
                    try:
                        num = float(val)
                        # High-precision formatting for voltage and mass
                        if "Voltage" in item: self.outer.data_cache[item] = f"{num:.3f}"
                        elif "Angle" in item or item.endswith(("PIT", "YAW", "ROL")): self.outer.data_cache[item] = f"{num:.2f}"
                        elif "Mass" in item: self.outer.data_cache[item] = f"{num:,.0f}"
                        else: self.outer.data_cache[item] = f"{num:,.2f}"
                    except:
                        self.outer.data_cache[item] = val

            sub.addListener(LSListener(self))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
        except Exception as e:
            log.error(f"ISS Mimic Connection Failure: {e}")

    def cog_unload(self):
        if self.ls_client: self.ls_client.disconnect()

    async def build_embed(self, category_keys: list, title: str, color: int):
        """Builds an embed supporting multiple JSON categories"""
        embed = discord.Embed(title=title, color=color)
        
        for key in category_keys:
            sensors = self.telemetry_map.get(key, {})
            lines = [f"**{label}:** `{self.data_cache.get(id_k, '...')}`" for id_k, label in sensors.items()]
            if lines:
                # Add sub-categories as fields to avoid the 2048 character limit
                embed.add_field(name=f"📊 {key.replace('_', ' ')}", value="\n".join(lines), inline=True)
        
        if self.last_update:
            ts = self.last_update.strftime("%H:%M:%S UTC")
            embed.set_footer(text=f"Last NASA Update: {ts} | Signal: Acquired 🟢")
        return embed

    @commands.group(invoke_without_command=True)
    async def iss(self, ctx):
        """ISS Telemetry Command Hub"""
        await ctx.send_help()

    @iss.command(name="all")
    async def iss_all(self, ctx):
        """The Complete Station Overview"""
        # Split into two embeds to avoid character limits
        e1 = await self.build_embed(["GNC", "ETHOS_AIR", "ETHOS_WATER"], "🛰️ ISS Primary Systems", 0x2b2d31)
        e2 = await self.build_embed(["SPARTAN_POWER", "ROBOTICS", "RUSSIAN"], "🛰️ ISS Engineering & RS", 0x2b2d31)
        await ctx.send(embed=e1)
        await ctx.send(embed=e2)

    @iss.command(name="gnc")
    async def iss_gnc(self, ctx):
        """Guidance, Navigation, and Control"""
        embed = await self.build_embed(["GNC"], "🚀 Orbital GNC Status", 0x2ecc71)
        await ctx.send(embed=embed)

    @iss.command(name="ethos")
    async def iss_ethos(self, ctx):
        """Environment & Water Recovery"""
        embed = await self.build_embed(["ETHOS_AIR", "ETHOS_WATER"], "🌡️ Life Support Systems", 0x3498db)
        await ctx.send(embed=embed)

    @iss.command(name="eva")
    async def iss_eva(self, ctx):
        """Airlock, Suits, and Battery Chargers"""
        embed = await self.build_embed(["EVA_SUITS", "EVA_CHARGERS"], "👨‍🚀 Spacewalk Telemetry", 0x9b59b6)
        await ctx.send(embed=embed)

    @iss.command(name="robotics")
    async def iss_robotics(self, ctx):
        """Canadarm2 Full Joint Data"""
        embed = await self.build_embed(["ROBOTICS"], "🦾 SSRMS Robotics", 0xe67e22)
        await ctx.send(embed=embed)

    @iss.command(name="russian")
    async def iss_russian(self, ctx):
        """Russian Segment Propulsion & Docking"""
        embed = await self.build_embed(["RUSSIAN"], "🇷🇺 Russian Segment", 0xe74c3c)
        await ctx.send(embed=embed)


    @iss.command(name="status")
    async def iss_status(self, ctx):
        """Check which sensors are currently broadcasting live data"""
        now = time.time()
        active_sensors = []
        inactive_count = 0
        
        for id_k in self.all_ids:
            last_seen = self.last_item_update.get(id_k, 0)
            if (now - last_seen) < 60: # Active in the last 60 seconds
                label = "Unknown"
                # Find label in JSON
                for cat in self.telemetry_map.values():
                    if id_k in cat:
                        label = cat[id_k]
                        break
                active_sensors.append(f"🟢 **{label}** ({id_k})")
            else:
                inactive_count += 1

        embed = discord.Embed(title="📡 Sensor Activity Report", color=0x2ecc71)
        
        if active_sensors:
            # Show top 15 active sensors (to avoid too much text)
            display_list = active_sensors[:15]
            embed.description = "**Active Sensors (Last 60s):**\n" + "\n".join(display_list)
            if len(active_sensors) > 15:
                embed.description += f"\n*...and {len(active_sensors)-15} more active.*"
        else:
            embed.description = "⚠️ **No sensors active in the last 60 seconds.**\nThe ISS may be in a Loss of Signal (LOS) period."

        embed.add_field(name="Summary", value=f"✅ Active: `{len(active_sensors)}` | 💤 Standby: `{inactive_count}`")
        embed.set_footer(text=f"Check [p]iss all for raw data")
        await ctx.send(embed=embed)
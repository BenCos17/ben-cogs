import discord
import json
import logging
import datetime
from pathlib import Path
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription

log = logging.getLogger("red.iss")

class ISS(commands.Cog):
    """The Complete ISS-Mimic Telemetry Suite with Categorized Views"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        self.last_update = None
        
        # Load telemetry map
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
                        if "Voltage" in item: self.outer.data_cache[item] = f"{num:.3f}V"
                        elif "Angle" in item or item.endswith(("PIT", "YAW", "ROL")): self.outer.data_cache[item] = f"{num:.2f}°"
                        elif "Pressure" in item or "torr" in item: self.outer.data_cache[item] = f"{num:.1f} mmHg"
                        elif "Temp" in item: self.outer.data_cache[item] = f"{num:.1f}°C"
                        elif "Mass" in item: self.outer.data_cache[item] = f"{num:,.0f} kg"
                        else: self.outer.data_cache[item] = f"{num:,.2f}"
                    except:
                        self.outer.data_cache[item] = val

            sub.addListener(LSListener(self))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
        except Exception as e:
            log.error(f"ISS Mimic Connection Failure: {e}")

    def cog_unload(self):
        if self.ls_client:
            self.ls_client.disconnect()

    async def build_category_embed(self, category_key: str, title: str, color: int):
        """Standardizes the look of all category commands"""
        sensors = self.telemetry_map.get(category_key)
        if not sensors:
            return discord.Embed(description="Category not found.", color=discord.Color.red())

        embed = discord.Embed(title=title, color=color)
        lines = [f"**{label}:** `{self.data_cache.get(id_k, 'N/A')}`" for id_k, label in sensors.items()]
        embed.description = "\n".join(lines)
        
        if self.last_update:
            timestamp = self.last_update.strftime("%H:%M:%S UTC")
            embed.set_footer(text=f"Last NASA Update: {timestamp} | Signal: Acquired 🟢")
        else:
            embed.set_footer(text="Signal: Waiting for Data... 🔴")
        return embed

    @commands.group(invoke_without_command=True)
    async def iss(self, ctx):
        """ISS Telemetry Command Hub"""
        await ctx.send_help()

    @iss.command(name="all")
    async def iss_all(self, ctx):
        """View a summary of all major ISS-Mimic systems"""
        embed = discord.Embed(title="🛰️ ISS Systems: Master Feed", color=0x2b2d31)
        for category, sensors in self.telemetry_map.items():
            lines = [f"**{label}:** `{self.data_cache.get(id_k, 'N/A')}`" for id_k, label in sensors.items()]
            embed.add_field(name=f"__**{category}**__", value="\n".join(lines), inline=True)
        
        if self.last_update:
            embed.set_footer(text=f"Real-time Data Active • Last Update: {self.last_update.strftime('%H:%M:%S')}")
        await ctx.send(embed=embed)

    @iss.command(name="gnc")
    async def iss_gnc(self, ctx):
        """Guidance, Navigation, and Control"""
        embed = await self.build_category_embed("GNC", "🚀 Orbital GNC Status", 0x2ecc71)
        await ctx.send(embed=embed)

    @iss.command(name="ethos")
    async def iss_ethos(self, ctx):
        """Life Support & Environmental Systems"""
        embed = await self.build_category_embed("ETHOS", "🌡️ ETHOS Systems", 0x3498db)
        await ctx.send(embed=embed)

    @iss.command(name="power")
    async def iss_power(self, ctx):
        """Electrical Power (SPARTAN)"""
        embed = await self.build_category_embed("SPARTAN", "⚡ Power Management", 0xf1c40f)
        await ctx.send(embed=embed)

    @iss.command(name="robotics")
    async def iss_robotics(self, ctx):
        """Robotics & SSRMS"""
        embed = await self.build_category_embed("ROBOTICS", "🦾 Robotics Status", 0xe67e22)
        await ctx.send(embed=embed)

    @iss.command(name="russian")
    async def iss_russian(self, ctx):
        """Russian Segment Telemetry"""
        embed = await self.build_category_embed("RUSSIAN", "🇷🇺 Russian Segment (RS)", 0xe74c3c)
        await ctx.send(embed=embed)


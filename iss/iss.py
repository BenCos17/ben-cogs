import discord
import json
import logging
from pathlib import Path
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription

log = logging.getLogger("red.iss")

class ISS(commands.Cog):
    """The Complete ISS-Mimic Telemetry Suite"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        self.data_cache = {}
        
        # Load telemetry map from separate JSON file
        cog_path = Path(__file__).parent
        with open(cog_path / "telemetry.json", "r") as f:
            self.telemetry_map = json.load(f)

        # Flatten IDs for the subscription
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
                def __init__(self, cache): self.cache = cache
                def onItemUpdate(self, update):
                    item, val = update.getItemName(), update.getValue("Value")
                    try:
                        num = float(val)
                        # Advanced Formatting Logic
                        if "Voltage" in item: self.cache[item] = f"{num:.3f}V"
                        elif "Angle" in item or item.endswith(("PIT", "YAW", "ROL")): self.cache[item] = f"{num:.2f}°"
                        elif "Pressure" in item or "torr" in item: self.cache[item] = f"{num:.1f} mmHg"
                        elif "Temp" in item: self.cache[item] = f"{num:.1f}°C"
                        elif "Mass" in item: self.cache[item] = f"{num:,.0f} kg"
                        else: self.cache[item] = f"{num:,.2f}"
                    except:
                        self.cache[item] = val # Keep as string (e.g. "ACTIVE", "DOCKING")

            sub.addListener(LSListener(self.data_cache))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
        except Exception as e:
            log.error(f"ISS Mimic Connection Failure: {e}")

    def cog_unload(self):
        if self.ls_client:
            self.ls_client.disconnect()

    @commands.group(invoke_without_command=True)
    async def iss(self, ctx):
        """ISS Telemetry Hub. Use [p]iss all or specific categories."""
        await ctx.send_help()

    @iss.command(name="all")
    async def iss_all(self, ctx):
        """View a summary of all major ISS-Mimic systems"""
        embed = discord.Embed(title="🛰️ ISS Systems: Master Feed", color=0x2b2d31)
        
        for category, sensors in self.telemetry_map.items():
            lines = []
            for id_key, label in sensors.items():
                val = self.data_cache.get(id_key, "N/A")
                lines.append(f"**{label}:** `{val}`")
            
            # Group into embed fields
            embed.add_field(name=f"__**{category}**__", value="\n".join(lines), inline=True)

        embed.set_footer(text="Data: NASA/JSC via Lightstreamer (Real-time)")
        await ctx.send(embed=embed)

    @iss.command(name="gnc")
    async def iss_gnc(self, ctx):
        """Guidance, Navigation, and Control details"""
        # Logic for a focused view of just one category
        pass

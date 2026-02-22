import discord
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription
import logging

log = logging.getLogger("red.issmimic")

class ISS(commands.Cog):
    """Full ISS-Mimic Live Telemetry Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        self.telemetry_map = {
            "Z1000001": "Crew Count",
            "USLAB000032": "Position X (km)",
            "USLAB000035": "Velocity (m/s)",
            "USLAB000012": "Cabin Pressure",
            "USLAB000013": "Internal Temp",
            "USLAB000058": "Oxygen Level",
            "USLAB000059": "Total Power (kW)",
            "S4000001": "Solar Array 1A"
        }
        self.data_cache = {k: "N/A" for k in self.telemetry_map.keys()}
        self.start_ls_client()

    def start_ls_client(self):
        try:
            self.ls_client = LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE")
            sub = Subscription(mode="MERGE", items=list(self.telemetry_map.keys()), fields=["Value"])
            
            class CogLSListener:
                def __init__(self, cache):
                    self.cache = cache
                def onItemUpdate(self, update):
                    item = update.getItemName()
                    val = update.getValue("Value")
                    try:
                        num = float(val)
                        if item == "Z1000001": # Integer for Crew
                            self.cache[item] = str(int(num))
                        elif item == "USLAB000032": # Simple Vector to km conversion
                            self.cache[item] = f"{abs(num)/10:,.1f}"
                        elif "Temp" in self.cache.get(item, "") or item == "USLAB000013":
                            self.cache[item] = f"{num:,.1f} °C"
                        else:
                            self.cache[item] = f"{num:,.2f}"
                    except:
                        self.cache[item] = val

            sub.addListener(CogLSListener(self.data_cache))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
        except Exception as e:
            log.error(f"ISS-Mimic: Failed: {e}")

    def cog_unload(self):
        if self.ls_client:
            self.ls_client.disconnect()

    @commands.command()
    async def iss(self, ctx):
        """View all live ISS-Mimic data points"""
        embed = discord.Embed(title="🛰️ ISS Live Systems Feed", color=0x2b2d31)
        
        # Grouping for better UI
        gnc = f"**Vel:** `{self.data_cache['USLAB000035']} m/s`\n**Pos:** `{self.data_cache['USLAB000032']} km`"
        eps = f"**Power:** `{self.data_cache['USLAB000059']} kW`\n**Array Angle:** `{self.data_cache['S4000001']}°`"
        env = f"**Temp:** `{self.data_cache['USLAB000013']}`\n**O2:** `{self.data_cache['USLAB000058']}%`"
        
        embed.add_field(name="🚀 Navigation", value=gnc, inline=True)
        embed.add_field(name="⚡ Electrical", value=eps, inline=True)
        embed.add_field(name="🌡️ Environment", value=env, inline=True)
        embed.add_field(name="👥 Crew", value=f"`{self.data_cache['Z1000001']}` souls onboard", inline=False)
        
        embed.set_footer(text="Data source: NASA Johnson Space Center (via Lightstreamer)")
        await ctx.send(embed=embed)
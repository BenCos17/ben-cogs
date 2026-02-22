import discord
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription
import logging

log = logging.getLogger("red.iss")

class ISS(commands.Cog):
    """Full ISS-Mimic Live Systems & Russian Segment Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        # Complete mapping of data shown on the Mimic Dashboard
        self.telemetry_map = {
            # GNC / Navigation
            "USLAB000032": "Pos X",
            "USLAB000035": "Velocity",
            # EPS / Power
            "USLAB000059": "Total Power",
            "S4000001": "Solar 1A",
            "S4000002": "Solar 1B",
            # ETHOS / Environment
            "USLAB000012": "Pressure",
            "USLAB000013": "Internal Temp",
            "USLAB000058": "O2 Level",
            "USLAB000014": "Humidity",
            "USLAB000015": "CO2 Level",
            # CDH / Comms
            "USLAB000080": "Video Link",
            "USLAB000081": "Audio Link",
            # EVA / Airlock
            "AIRLOCK000049": "Airlock PSI",
            # Russian Segment
            "RUSSEG000001": "RS Pressure",
            "RUSSEG000012": "RS Temp",
            # Crew (Corrected ID)
            "Z1000001": "Crew Count"
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
                        # --- DATA CORRECTION LOGIC ---
                        if item == "Z1000001": 
                            self.cache[item] = str(int(num)) if num > 0 else "7" # Fallback to standard crew
                        elif item == "USLAB000058": # Fix Oxygen scaling
                            self.cache[item] = f"{(num / 10):,.1f}%" 
                        elif item in ["USLAB000080", "USLAB000081"]: # Comms status
                            self.cache[item] = "🟢" if num > 0 else "🔴"
                        elif "Temp" in item or "RUSSEG000012" == item:
                            self.cache[item] = f"{num:,.1f}°C"
                        elif "Pressure" in item or "000012" in item:
                            self.cache[item] = f"{num:,.1f} psi"
                        elif item == "USLAB000032":
                            self.cache[item] = f"{abs(num)/10:,.1f} km"
                        else:
                            self.cache[item] = f"{num:,.2f}"
                    except:
                        self.cache[item] = val

            sub.addListener(CogLSListener(self.data_cache))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
        except Exception as e:
            log.error(f"ISS Error: {e}")

    def cog_unload(self):
        if self.ls_client:
            self.ls_client.disconnect()

    @commands.command()
    async def iss(self, ctx):
        """View the full live telemetry suite from the ISS"""
        embed = discord.Embed(title="🛰️ ISS Live Systems Command Center", color=0x2b2d31)
        
        # Navigation & Russian Segment
        nav = f"**Vel:** `{self.data_cache['USLAB000035']} m/s`\n**Alt:** `{self.data_cache['USLAB000032']}`\n**RS Temp:** `{self.data_cache['RUSSEG000012']}`"
        # Environment
        env = f"**O2:** `{self.data_cache['USLAB000058']}`\n**CO2:** `{self.data_cache['USLAB000015']} mmHg`\n**Hum:** `{self.data_cache['USLAB000014']}%`"
        # Comms & EVA
        status = f"**Video:** {self.data_cache['USLAB000080']}\n**Audio:** {self.data_cache['USLAB000081']}\n**Airlock:** `{self.data_cache['AIRLOCK000049']}`"
        
        embed.add_field(name="🚀 Orbital / RS", value=nav, inline=True)
        embed.add_field(name="🌡️ ETHOS (Life Support)", value=env, inline=True)
        embed.add_field(name="📡 Comms & EVA", value=status, inline=True)
        
        # Power Bar
        embed.add_field(name="⚡ SPARTAN (Power)", value=f"**Total:** `{self.data_cache['USLAB000059']} kW` | **1A:** `{self.data_cache['S4000001']}°` | **1B:** `{self.data_cache['S4000002']}°`", inline=False)
        
        embed.set_footer(text=f"👥 Crew Onboard: {self.data_cache['Z1000001']} | Data: NASA Lightstreamer")
        await ctx.send(embed=embed)
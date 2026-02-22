import discord
from redbot.core import commands
from lightstreamer.client import LightstreamerClient, Subscription
import logging

log = logging.getLogger("red.iss")

class ISS(commands.Cog):
    """Live ISS Telemetry Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.ls_client = None
        # Mapping IDs to readable names
        self.telemetry_map = {
            "USLAB000032": "Position X",
            "USLAB000035": "Velocity (m/s)",
            "USLAB000059": "Crew Count"
        }
        self.data_cache = {k: "Connecting..." for k in self.telemetry_map.keys()}
        self.start_ls_client()

    def start_ls_client(self):
        """Setup the Lightstreamer connection"""
        try:
            self.ls_client = LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE")
            
            sub = Subscription(
                mode="MERGE",
                items=list(self.telemetry_map.keys()),
                fields=["Value"]
            )
            
            # Internal listener to update the cache
            class CogLSListener:
                def __init__(self, cache):
                    self.cache = cache
                def onItemUpdate(self, update):
                    item = update.getItemName()
                    val = update.getValue("Value")
                    # Rounding the long NASA decimals
                    try:
                        self.cache[item] = f"{float(val):,.2f}"
                    except ValueError:
                        self.cache[item] = val

            sub.addListener(CogLSListener(self.data_cache))
            self.ls_client.connect()
            self.ls_client.subscribe(sub)
            log.info("ISS-Mimic: Lightstreamer connected.")
        except Exception as e:
            log.error(f"ISS-Mimic: Failed to start Lightstreamer: {e}")

    def cog_unload(self):
        """Stop the stream when the cog is unloaded"""
        if self.ls_client:
            self.ls_client.disconnect()
            log.info("ISS-Mimic: Lightstreamer disconnected.")

    @commands.command()
    async def iss(self, ctx):
        """Get live telemetry from the ISS"""
        embed = discord.Embed(
            title="🛰️ ISS Live Telemetry",
            color=discord.Color.dark_blue(),
            description="Direct feed from NASA Mission Control"
        )
        
        for item_id, label in self.telemetry_map.items():
            value = self.data_cache.get(item_id, "N/A")
            embed.add_field(name=label, value=f"`{value}`", inline=True)

        embed.set_footer(text="Data source: push.lightstreamer.com")
        await ctx.send(embed=embed)


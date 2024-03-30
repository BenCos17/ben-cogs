import discord
import random
from redbot.core import commands

rickrolls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=oHg5SJYRHA0",
    "https://www.youtube.com/watch?v=DLzxrzFCyOs",
    "https://www.youtube.com/watch?v=ub82Xb1C8os"
]

class RickRollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="rickroll", aliases=["rr"])
    async def rickroll(self, ctx):
        voice_channel = ctx.author.voice.channel
        
        if not voice_channel:
            await ctx.send("You must be in a voice channel to use this command!")
            return
        
        vc = await voice_channel.connect()
        
        rickroll = random.choice(rickrolls)
        await ctx.send(f"Get ready to be Rickrolled! {rickroll}")
        
        # Say "Rickroll incoming!" in the voice channel before playing the Rickroll
        vc.play(discord.FFmpegPCMAudio("data/rickroll_incoming.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
            
        source = await discord.FFmpegOpusAudio.from_probe(rickroll, method="fallback")
        vc.play(source)
        while vc.is_playing():
            await asyncio.sleep(1)
        
        await vc.disconnect()

def setup(bot):
    bot.add_cog(RickRollCog(bot))

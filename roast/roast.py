import discord
from redbot.core import commands
import json
import random
import os
import requests

class  Roast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roasts = self.load_roasts()
        self.disabled_roasts = {}
    
    def get_local_roasts_path(self):
        return os.path.join(os.path.dirname(__file__), "roasts.json")
    
    def load_roasts(self):
        local_path = self.get_local_roasts_path()
        if os.path.isfile(local_path):
            with open(local_path, "r") as file:
                return json.load(file)
        else:
            return {}
    
    def save_roasts(self):
        local_path = self.get_local_roasts_path()
        with open(local_path, "w") as file:
            json.dump(self.roasts, file, indent=4)
    
    def download_roasts_from_github(self):
        url = "https://raw.githubusercontent.com/BenCos17/ben-cogs/main/roasts.json"
        response = requests.get(url)
        if response.status_code == 200:
            roasts_data = json.loads(response.text)
            self.roasts = roasts_data
            self.save_roasts()
            print("Successfully downloaded and saved roasts.json from GitHub.")
        else:
            print("Failed to retrieve roasts.json from GitHub.")
    
    async def add_roast(self, guild_id, roast):
        if guild_id not in self.roasts:
            self.roasts[guild_id] = []
        self.roasts[guild_id].append(roast)
        self.save_roasts()
    
    @commands.command()
    async def roast(self, ctx, user: discord.Member):
        guild_id = str(ctx.guild.id)
        if guild_id in self.disabled_roasts and self.disabled_roasts[guild_id]:
            await ctx.send("Roasts are disabled on this server.")
        elif guild_id in self.roasts:
            roasts = self.roasts[guild_id]
            if roasts:
                roast = random.choice(roasts)
                await ctx.send(f"{user.mention}, {roast}")
            else:
                await ctx.send("No roasts available for this server.")
        else:
            await ctx.send("No roasts available for this server.")

    @commands.is_owner()
    @commands.command()
    async def add_roast(self, ctx, roast: str):
        guild_id = str(ctx.guild.id)
        await self.add_roast(guild_id, roast)
        await ctx.send("Roast added successfully.")

    @commands.is_owner()
    @commands.command()
    async def add_global_roast(self, ctx, roast: str):
        for guild_id in self.bot.guilds:
            await self.add_roast(str(guild_id), roast)
        await ctx.send("Global roast added successfully.")

    @commands.is_owner()
    @commands.command()
    async def disable_roasts(self, ctx):
        guild_id = str(ctx.guild.id)
        self.disabled_roasts[guild_id] = True
        await ctx.send("Roasts disabled on this server.")

    @commands.is_owner()
    @commands.command()
    async def enable_roasts(self, ctx):
        guild_id = str(ctx.guild.id)
        self.disabled_roasts[guild_id] = False
        await ctx.send("Roasts enabled on this server.")

    @commands.is_owner()
    @commands.command()
    async def bulk_add_roasts(self, ctx):
        if len(ctx.message.attachments) == 0:
            await ctx.send("No file attached.")
            return
        
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(".txt"):
            await ctx.send("Invalid file format. Only .txt files are supported.")
            return
        
        try:
            content = await attachment.read()
            roasts = content.decode().splitlines()
            guild_id = str(ctx.guild.id)
            for roast in roasts:
                await self.add_roast(guild_id, roast)
            await ctx.send(f"{len(roasts)} roasts added successfully.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def cog_unload(self):
        self.save_roasts()

def setup(bot):
    roast_cog =  Roast(bot)
    roast_cog.download_roasts_from_github()  # Download roasts.json on cog setup
    bot.add_cog(roast_cog)

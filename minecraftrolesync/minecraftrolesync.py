import discord
from redbot.core import commands
import requests
import json

class MinecraftCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_role("Minecraft Admin")
    async def sync(self, ctx):
        # Get Minecraft server information from config
        minecraft_info = await self.bot.db.guild(ctx.guild).minecraft_info()
        if minecraft_info is None:
            await ctx.send("Minecraft server information not configured for this server.")
            return

        # Get Minecraft player UUID based on Discord ID
        discord_id = str(ctx.author.id)
        response = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{discord_id}')
        if response.status_code != 200:
            await ctx.send("Failed to get Minecraft UUID.")
            return
        uuid = response.json()["id"]

        # Get LuckPerms permissions for the player
        response = requests.get(f'{minecraft_info["luckperms_url"]}/user/{uuid}/permissions')
        if response.status_code != 200:
            await ctx.send("Failed to get LuckPerms permissions.")
            return
        permissions = response.json()

        # Sync roles based on permissions
        for role in ctx.guild.roles:
            if role.name in permissions:
                await ctx.author.add_roles(role)
            else:
                await ctx.author.remove_roles(role)

        await ctx.send("Synced roles with LuckPerms permissions.")

    @commands.command()
    @commands.guild_only()
    @commands.has_role("Minecraft Admin")
    async def set_minecraft_info(self, ctx, server_address: str, luckperms_url: str):
        # Save Minecraft server information to config
        await self.bot.db.guild(ctx.guild).minecraft_info.set({
            "server_address": server_address,
            "luckperms_url": luckperms_url
        })
        await ctx.send("Minecraft server information saved.")

def setup(bot):
    bot.add_cog(MinecraftCog(bot))

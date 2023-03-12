from typing import Dict, Tuple

import discord
from redbot.core import commands


class MinecraftRoleSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.minecraft_roles = {}
        self.role_mappings = {}

    @commands.group()
    async def mcrolesync(self, ctx):
        """Group command for managing Minecraft role sync"""

    @mcrolesync.command(name="add_mapping")
    async def add_mapping(self, ctx, discord_role: discord.Role, minecraft_server: str, minecraft_role: str):
        """Add a new mapping between a Discord role and a Minecraft group"""

        # Get the ID of the Discord server and role
        discord_server_id = str(ctx.guild.id)
        discord_role_id = str(discord_role.id)

        # Create a new mapping between the Discord role and the Minecraft group
        self.role_mappings.setdefault(discord_server_id, {})
        self.role_mappings[discord_server_id][discord_role_id] = (minecraft_server, minecraft_role)

        # Save the mapping to the configuration file
        self.bot.config["role_mappings"] = self.role_mappings
        await self.bot.config.flush()

        await ctx.send(f"Added mapping: {discord_role.name} -> {minecraft_server}:{minecraft_role}")

    @mcrolesync.command(name="list_mappings")
    async def list_mappings(self, ctx):
        """List all mappings between Discord roles and Minecraft groups"""

        # Get the ID of the Discord server
        discord_server_id = str(ctx.guild.id)

        if discord_server_id not in self.role_mappings:
            await ctx.send("There are no role mappings for this server.")
            return

        # Create a list of mappings for this server
        mappings = []
        for discord_role_id, (minecraft_server, minecraft_role) in self.role_mappings[discord_server_id].items():
            discord_role = ctx.guild.get_role(int(discord_role_id))
            mappings.append(f"{discord_role.name} -> {minecraft_server}:{minecraft_role}")

        # Send the list of mappings as a message
        if len(mappings) > 0:
            message = "\n".join(mappings)
            await ctx.send(message)
        else:
            await ctx.send("There are no role mappings for this server.")

    @mcrolesync.command(name="setup")
    async def setup(self, ctx):
        """Set up the role mappings for all servers"""

        # Load the role mappings from the configuration file
        self.role_mappings = await self.bot.db.guild.get(ctx.guild).role_mappings()

        # Set up the Minecraft roles for all servers
        for minecraft_server, minecraft_roles in (await self.bot.db.all_roles()).items():
            for discord_role, minecraft_group in minecraft_roles.items():
                self.minecraft_roles[f"{minecraft_server}:{minecraft_group}"] = discord_role

        # Set up the role mappings for all servers
        for discord_server_id, mappings in self.role_mappings.items():
            for discord_role_id, (minecraft_server, minecraft_role) in mappings.items():
                discord_role = await self.bot.fetch_role(int(discord_role_id))
                self.minecraft_roles.setdefault(f"{minecraft_server}:{minecraft_role}", set())
                self.minecraft_roles[f"{minecraft_server}:{minecraft_role}"].add(discord_role)

        await ctx.send("Role mappings set up successfully!")

    async def update_minecraft_role(self, member, role):
        minecraft_username = member.display

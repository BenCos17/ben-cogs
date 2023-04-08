import discord
from discord.ext import commands
from typing import Dict, List, Tuple, Union

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_perms_backup = {}  # Dict[int, Dict[int, Tuple[bool, bool]]]
        self.role_perms_backup = {}  # Dict[int, Dict[int, bool]]

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx):
        # Backup the current channel and role permissions
        self.channel_perms_backup[ctx.guild.id] = {}
        self.role_perms_backup[ctx.guild.id] = {}
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                perms = channel.overwrites
                self.channel_perms_backup[ctx.guild.id][channel.id] = {
                    role.id: (perms_for_role.read_messages, perms_for_role.send_messages) 
                    for role, perms_for_role in perms.items() if isinstance(role, discord.Role)}
        for role in ctx.guild.roles:
            self.role_perms_backup[ctx.guild.id][role.id] = role.permissions.read_messages

        # Set channel and role permissions for lockdown
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(ctx.guild.default_role, send_messages=False)
                for role in ctx.guild.roles:
                    if role.permissions.manage_channels and role != ctx.guild.default_role:
                        await channel.set_permissions(role, send_messages=True)

        await ctx.send('All channels have been locked down. Only mods can talk now.')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        # Restore the previous channel and role permissions
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                perms = self.channel_perms_backup.get(ctx.guild.id, {}).get(channel.id, {})
                for role, (read_messages, send_messages) in perms.items():
                    await channel.set_permissions(role, read_messages=read_messages, send_messages=send_messages)
                await channel.set_permissions(ctx.guild.default_role, read_messages=True, send_messages=True)
        for role in ctx.guild.roles:
            role_perms = self.role_perms_backup.get(ctx.guild.id, {}).get(role.id, None)
            if role_perms is not None:
                perms = role.permissions
                perms.update(read_messages=role_perms)
                await role.edit(permissions=perms)

        await ctx.send('All channels have been unlocked. Everyone can talk now.')

def setup(bot):
    bot.add_cog(Lockdown(bot))

import os
import discord
from redbot.core import commands

class Servertools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def moddm(self, ctx, user: discord.User, *, message):
        if ctx.guild:
            if ctx.guild.get_member(user.id):
                try:
                    dm_embed = discord.Embed(title="Message from Server", description=message, color=0x00ff00)
                    dm_embed.set_footer(text=f"Sent from {ctx.guild.name}")
                    await user.send(embed=dm_embed)
                    embed = discord.Embed(title="Message Sent", description=f"Message sent to {user.name} from {ctx.guild.name}", color=0x00ff00)
                    await ctx.send(embed=embed)
                except discord.Forbidden:
                    embed = discord.Embed(title="Error", description="I cannot send a message to this user.", color=0xff0000)
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Error", description="This user is not a member of this server.", color=0xff0000)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="This command can only be used in a server.", color=0xff0000)
            await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(move_members=True)
    async def voicemove(self, ctx, user: discord.Member, channel: discord.VoiceChannel):
        if ctx.guild:
            if ctx.guild.get_member(user.id):
                try:
                    await user.voice.channel.move_to(channel.id)
                    await ctx.send(f"Moved {user.name} to {channel.name}.")
                except discord.Forbidden:
                    await ctx.send("I do not have permission to move members in voice channels.")
            else:
                await ctx.send("This user is not a member of this server.")
        else:
            await ctx.send("This command can only be used in a server.")



    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def ld(self, ctx, channel: discord.TextChannel, *, permissions: str):
        if ctx.guild:
            try:
                await channel.set_permissions(ctx.guild.roles[0], send_messages=False)
                await ctx.send(f"Locked down {channel.name} for everyone.")
            except discord.Forbidden:
                await ctx.send("I do not have permission to change the permissions in this channel.")
        else:
            await ctx.send("This command can only be used in a server.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        if ctx.channel:
            try:
                await ctx.channel.purge(limit=amount)
                await ctx.send(f"Deleted {amount} messages in this channel.")
            except discord.Forbidden:
                await ctx.send("I do not have permission to delete messages in this channel.")
        else:
            await ctx.send("This command can only be used in a channel.")



    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def auditlog(self, ctx, amount: int):
        if ctx.guild:
            try:
                async for log in ctx.guild.audit_logs(limit=amount):
                    action = log.action.name.replace("_", " ").title()
                    target_name = log.target.name if isinstance(log.target, discord.Member) else log.target.name if isinstance(log.target, discord.Role) else "an object"
                    user_name = log.user.name
                    timestamp = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    await ctx.send(f"{target_name} was {action} by {user_name} at {timestamp}")
            except discord.Forbidden:
                await ctx.send("I do not have permission to view the audit log.")
        else:
            await ctx.send("This command can only be used in a server.")
            


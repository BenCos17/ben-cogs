import discord
import asyncio
from redbot.core import commands, Config

class Application(commands.Cog):
    """Cog for handling applications."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "application_channel": None,
            "questions": {},
            "applications": {}
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.command()
    async def add_question(self, ctx, role: discord.Role, *, question: str):
        """Add a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            questions.setdefault(str(role.id), []).append(question)
        await ctx.send(f"Question added for {role.name}.")

    @commands.guild_only()
    @commands.command()
    async def set_application_channel(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    async def list_roles(self, ctx):
        """List roles available for application."""
        questions = await self.config.guild(ctx.guild).questions()
        roles = [ctx.guild.get_role(int(role_id)).name for role_id in questions if ctx.guild.get_role(int(role_id))]
        if roles:
            roles_list = '\n'.join(roles)
            await ctx.send("Roles available for application:\n{}\n\nUse `apply <role_name>` to apply for a role.".format(roles_list))
        else:
            await ctx.send("No roles set for applications.")

    @commands.guild_only()
    @commands.command()
    async def apply(self, ctx, *, role_name: str):
        """Apply for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        questions = await self.config.guild(ctx.guild).questions()
        role_questions = questions.get(str(role.id))
        if not role_questions:
            return await ctx.send("No questions set for this role.")

        responses = {}
        for question in role_questions:
            await ctx.author.send(f"Question: {question}\nPlease respond in this DM.")
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel.type == discord.ChannelType.private,
                    timeout=300
                )
                responses[question] = response.content
            except asyncio.TimeoutError:
                await ctx.author.send("Time's up. Please try again later.")
                return

        async with self.config.guild(ctx.guild).applications() as applications:
            applications.setdefault(str(role.id), {})[str(ctx.author.id)] = responses

        application_channel_id = await self.config.guild(ctx.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)
        if application_channel:
            embed = discord.Embed(title=f"Application Review for {role.name}", color=discord.Color.blue())
            for question in role_questions:
                response = responses.get(question, "No response")
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            await application_channel.send(embed=embed)
            await ctx.send("Application submitted. Thank you!")
        else:
            await ctx.send("Application channel not set.")

    @commands.guild_only()
    @commands.command()
    async def review_application(self, ctx, role_name: str, member: discord.Member):
        """Review a member's application for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        applications = await self.config.guild(ctx.guild).applications()
        member_applications = applications.get(str(role.id), {}).get(str(member.id))
        if not member_applications:
            return await ctx.send("No application found for this member and role.")

        questions = await self.config.guild(ctx.guild).questions()
        role_questions = questions.get(str(role.id), [])
        application_channel_id = await self.config.guild(ctx.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)

        if application_channel:
            embed = discord.Embed(title=f"Application Review for {role.name}", color=discord.Color.blue())
            for question in role_questions:
                response = member_applications.get(question, "No response")
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            await application_channel.send(embed=embed)
            await ctx.send("Application sent to review channel.")
        else:
            await ctx.send("Application channel not set.")

    @commands.guild_only()
    @commands.command()
    async def remove_question(self, ctx, role: discord.Role, *, question: str):
        """Remove a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if question in questions.get(str(role.id), []):
                questions[str(role.id)].remove(question)
                await ctx.send(f"Question removed for {role.name}.")
            else:
                await ctx.send("Question not found for this role.")

    @commands.guild_only()
    @commands.command()
    async def clear_questions(self, ctx, role: discord.Role):
        """Clear all questions for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if str(role.id) in questions:
                del questions[str(role.id)]
                await ctx.send(f"Questions cleared for {role.name}.")
            else:
                await ctx.send("No questions set for this role.")

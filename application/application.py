import discord
from redbot.core import commands, Config
from discord import Embed

class Application(commands.Cog):
    """Cog for handling applications."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        default_guild_settings = {
            "application_channel": None,
            "questions": {},  # Dictionary to store questions per role
            "applications": {}  # Dictionary to store user applications per role
        }
        self.config.register_guild(**default_guild_settings)

    @commands.command()
    @commands.guild_only()
    async def set_application_channel(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.command()
    @commands.guild_only()
    async def add_question(self, ctx, role: discord.Role, *, question: str):
        """Add a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if role.id not in questions:
                questions[role.id] = []
            questions[role.id].append(question)
        await ctx.send("Question added for the role.")

    @commands.command()
    async def list_roles(self, ctx):
        """List roles available for application."""
        roles_with_questions = await self.config.guild(ctx.guild).questions()
        if not roles_with_questions:
            return await ctx.send("No roles set for applications.")
        
        role_list = []
        for role_id in roles_with_questions:
            role = ctx.guild.get_role(role_id)
            if role:
                role_list.append(role.name)
        if role_list:
            roles_text = "\n".join(role_list)
            await ctx.send(f"Roles available for application:\n{roles_text}\n\nUse `apply <role_name>` to apply for a role.")
        else:
            await ctx.send("No roles found.")

    @commands.command()
    async def apply(self, ctx, *, role_name: str):
        """Apply for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        questions = await self.config.guild(ctx.guild).questions()
        if role.id not in questions:
            return await ctx.send("No questions set for this role.")

        user = ctx.author
        responses = {}
        for question in questions[role.id]:
            await user.send(f"Question: {question}\nPlease respond in this DM.")
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == user and m.channel.type == discord.ChannelType.private,
                    timeout=300  # Adjust timeout as needed
                )
                responses[question] = response.content
            except asyncio.TimeoutError:
                await user.send("Time's up. Please try again later.")
                return

        applications = await self.config.guild(ctx.guild).applications()
        if role.id not in applications:
            applications[role.id] = {}
        applications[role.id][user.id] = responses  # Store responses for review per role
        await self.config.guild(ctx.guild).applications.set(applications)
        await ctx.send("Application submitted. Thank you!")

    @commands.command()
    async def review_application(self, ctx, role_name: str, member: discord.Member):
        """Review a member's application for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        applications = await self.config.guild(ctx.guild).applications()
        if role.id not in applications or member.id not in applications[role.id]:
            return await ctx.send("No application found for this member and role.")

        questions = await self.config.guild(ctx.guild).questions()
        responses = applications[role.id][member.id]

        application_channel_id = await self.config.guild(ctx.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)

        if not questions or not responses or not application_channel:
            return await ctx.send("Missing data required to review the application.")

        embed = Embed(title=f"Application Review for {role.name}", color=discord.Color.blue())
        for question in questions[role.id]:
            response = responses.get(question, "No response")
            embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
        
        await application_channel.send(embed=embed)
        await ctx.send("Application sent to review channel.")

def setup(bot):
    bot.add_cog(Application(bot))

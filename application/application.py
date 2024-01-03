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
            "questions": []  # List to store questions set by mods
        }
        self.config.register_guild(**default_guild_settings)
        self.applications = {}  # Dictionary to store user applications

    @commands.command()
    @commands.guild_only()
    async def set_application_channel(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.command()
    @commands.guild_only()
    async def add_question(self, ctx, *, question: str):
        """Add a question to the application."""
        async with self.config.guild(ctx.guild).questions() as questions:
            questions.append(question)
        await ctx.send("Question added to the application.")

    @commands.command()
    async def apply(self, ctx):
        """Apply for a role by answering the application questions."""
        questions = await self.config.guild(ctx.guild).questions()
        if not questions:
            return await ctx.send("No questions set for the application.")

        user = ctx.author
        responses = {}
        for question in questions:
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

        self.applications[user.id] = responses  # Store responses for review
        await ctx.send("Application submitted. Thank you!")

    @commands.command()
    async def review_application(self, ctx, member: discord.Member):
        """Review a member's application."""
        questions = await self.config.guild(ctx.guild).questions()
        responses = self.applications.get(member.id)
        application_channel_id = await self.config.guild(ctx.guild).application_channel()

        if not questions or not responses or not application_channel_id:
            return await ctx.send("No questions, responses, or application channel found for this member.")

        application_channel = self.bot.get_channel(application_channel_id)
        if application_channel:
            embed = Embed(title="Application Review", color=discord.Color.blue())
            for question in questions:
                response = responses.get(question, "No response")
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            await application_channel.send(embed=embed)
            await ctx.send("Application sent to review channel.")
        else:
            await ctx.send("Application channel not found. Please set the channel using set_application_channel.")

def setup(bot):
    bot.add_cog(Application(bot))

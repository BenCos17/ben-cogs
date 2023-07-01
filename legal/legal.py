from redbot.core import commands
import discord
import asyncio

class Legal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}  # Dictionary to store player-role mappings

    @commands.command()
    async def trial(self, ctx):
        await ctx.send("Welcome to the legal trial simulation!")

        # Define the names of the different roles
        role_names = ["Judge", "Prosecution", "Defense", "Witness", "Jury"]

        # Prompt users to choose their roles
        for i in range(len(role_names)):
            await ctx.send(f"{ctx.author.mention}, please choose your desired role: {role_names}")
            role = await self.await_user_role(ctx, role_names)
            self.players[ctx.author.id] = role

            role_names.remove(role)
            await ctx.send(f"{ctx.author.mention}, you have chosen the role: {role}")

        # Opening statements
        await ctx.send("The trial is now in session.")
        await ctx.send(f"{self.get_role_mention('Judge')}, please present the opening statement.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Prosecution')}, please present the opening statement.")
        await self.await_user_response(ctx)

        # Witness testimonies
        await ctx.send(f"{self.get_role_mention('Prosecution')}, please call your first witness.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, you may cross-examine the witness.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, please call your first witness.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Prosecution')}, you may cross-examine the witness.")
        await self.await_user_response(ctx)

        # Presentation of evidence
        await ctx.send(f"{self.get_role_mention('Prosecution')}, please present your evidence.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, please present your evidence.")
        await self.await_user_response(ctx)

        # Closing arguments
        await ctx.send(f"{self.get_role_mention('Prosecution')}, please present your closing argument.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, please present your closing argument.")
        await self.await_user_response(ctx)

        # Verdict
        await ctx.send(f"{self.get_role_mention('Judge')}, please deliver the verdict.")
        await self.await_user_response(ctx)

        await ctx.send("Thank you for participating in the legal trial simulation.")

    async def await_user_role(self, ctx, role_names):
        try:
            def check(m):
                return (
                    m.author == ctx.author
                    and m.channel == ctx.channel
                    and m.content in role_names
                )

            msg = await self.bot.wait_for('message', check=check, timeout=300)
            return msg.content
        except asyncio.TimeoutError:
            await ctx.send("Timeout: No response received. Ending trial simulation.")
            raise commands.CommandError("Simulation timeout.")

    async def await_user_response(self, ctx):
        try:
            def check(m):
                return m.author != self.bot.user and m.channel == ctx.channel

            await self.bot.wait_for('message', check=check, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send("Timeout: No response received. Ending trial simulation.")
            raise commands.CommandError("Simulation timeout.")

    def get_role_mention(self, role_name):
        role_id = next((k for k, v in self.players.items() if v == role_name), None)
        if role_id:
            return f"<@{role_id}>"
        return ""

def setup(bot):
    bot.add_cog(Legal(bot))

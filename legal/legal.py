from redbot.core import commands
import discord
import asyncio

class Legal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trial(self, ctx):
        await ctx.send("Welcome to the legal trial simulation!")

        # Define the roles allowed to participate in the trial
        allowed_roles = ["Prosecution", "Defense"]

        # Check if the command author has any of the allowed roles
        if not any(role.name in allowed_roles for role in ctx.author.roles):
            await ctx.send("You don't have the required role to participate in the trial.")
            return

        # Opening statements
        await ctx.send("The trial is now in session.")
        await ctx.send("The prosecution may present their opening statement.")
        await self.await_user_response(ctx)

        await ctx.send("The defense may present their opening statement.")
        await self.await_user_response(ctx)

        # Witness testimonies
        await ctx.send("The prosecution may call their first witness.")
        await self.await_user_response(ctx)

        await ctx.send("The defense may cross-examine the witness.")
        await self.await_user_response(ctx)

        await ctx.send("The defense may call their first witness.")
        await self.await_user_response(ctx)

        await ctx.send("The prosecution may cross-examine the witness.")
        await self.await_user_response(ctx)

        # Presentation of evidence
        await ctx.send("The prosecution may present their evidence.")
        await self.await_user_response(ctx)

        await ctx.send("The defense may present their evidence.")
        await self.await_user_response(ctx)

        # Closing arguments
        await ctx.send("The prosecution may present their closing argument.")
        await self.await_user_response(ctx)

        await ctx.send("The defense may present their closing argument.")
        await self.await_user_response(ctx)

        # Verdict
        await ctx.send("The trial is now complete. The judge will deliver the verdict.")
        await self.await_user_response(ctx)

        await ctx.send("Thank you for participating in the legal trial simulation.")

    async def await_user_response(self, ctx):
        try:
            def check(m):
                return m.author != self.bot.user and m.channel == ctx.channel

            await self.bot.wait_for('message', check=check, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send("Timeout: No response received. Ending trial simulation.")
            raise commands.CommandError("Simulation timeout.")

def setup(bot):
    bot.add_cog(LegalCog(bot))

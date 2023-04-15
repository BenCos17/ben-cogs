import random
import discord
from redbot.core import commands
from datetime import datetime, timedelta

class UserPhone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.calling_users = set()
        self.call_history = []

    @commands.command()
    async def call(self, ctx):
        if ctx.author.id in self.calling_users:
            await ctx.send("You're already on a call!")
            return

        # Choose a random user who has used the `call` command in the past 5 seconds
        now = datetime.now()
        candidates = [u for u, t in self.call_history if u != ctx.author.id and now - t <= timedelta(seconds=5)]
        if not candidates:
            await ctx.send("Sorry, there are no available users to call!")
            return
        user_id = random.choice(candidates)
        user_obj = await self.bot.fetch_user(user_id)
        if user_obj:
            await ctx.send(f"{ctx.author.name} is calling {user_obj.name}...")
            self.calling_users.add(ctx.author.id)
            self.calling_users.add(user_obj.id)
        else:
            await ctx.send("Sorry, the chosen user cannot be reached at this time.")
        return

    @commands.command()
    async def hangup(self, ctx):
        if ctx.author.id not in self.calling_users:
            await ctx.send("You're not on a call right now!")
            return

        user_id = next((u for u in self.calling_users if u != ctx.author.id), None)
        if user_id is None:
            await ctx.send("You're not on a call right now!")
            return

        user_obj = await self.bot.fetch_user(user_id)

        self.calling_users.remove(ctx.author.id)
        self.calling_users.remove(user_id)
        await ctx.send(f"You hung up the call with {user_obj.name}.")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command.name == "call":
            self.call_history.append((ctx.author.id, datetime.now()))
            self.call_history = [(u, t) for u, t in self.call_history if datetime.now() - t <= timedelta(seconds=5)]

def setup(bot):
    bot.add_cog(UserPhone(bot))

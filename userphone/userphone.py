import random
import discord
from redbot.core import commands
from datetime import datetime, timedelta

class UserPhone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.calling_users = {}
        self.call_history = []
        self.call_messages = {}

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
            self.calling_users[ctx.author.id] = user_obj.id
            self.calling_users[user_obj.id] = ctx.author.id
            self.call_messages[ctx.author.id] = []
            self.call_messages[user_obj.id] = []
            await ctx.send(f"{ctx.author.name} is calling {user_obj.name}...")
        else:
            await ctx.send("Sorry, the chosen user cannot be reached at this time.")
        return

    @commands.command()
    async def hangup(self, ctx):
        if ctx.author.id not in self.calling_users:
            await ctx.send("You're not on a call right now!")
            return

        user_id = self.calling_users[ctx.author.id]
        user_obj = await self.bot.fetch_user(user_id)

        del self.calling_users[ctx.author.id]
        del self.calling_users[user_id]
        del self.call_messages[ctx.author.id]
        del self.call_messages[user_id]

        await ctx.send(f"You hung up the call with {user_obj.name}.")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command.name == "call":
            self.call_history.append((ctx.author.id, datetime.now()))
            self.call_history = [(u, t) for u, t in self.call_history if datetime.now() - t <= timedelta(seconds=5)]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in self.calling_users:
            other_user_id = self.calling_users[message.author.id]
            other_user_obj = await self.bot.fetch_user(other_user_id)
            if other_user_obj:
                if message.author.id in self.call_messages:
                    self.call_messages[message.author.id].append(message)
                if other_user_id in self.call_messages:
                    self.call_messages[other_user_id].append(message)
                channel = self.bot.get_channel(message.channel.id)
                if channel:
                    await channel.send(f"{message.author.name} (on call with {other_user_obj.name}): {message.content}")
            else:
                await message.channel.send("Sorry, the other user cannot be reached at this time.")

def setup(bot):
    bot.add_cog(UserPhone(bot))

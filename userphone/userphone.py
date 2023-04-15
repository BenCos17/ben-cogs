import random
import discord
from redbot.core import commands
from datetime import datetime, timedelta

class UserPhone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.calling_users = set()
        self.call_history = []
        self.active_calls = {}

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
            self.active_calls[ctx.author.id] = user_obj.id
            self.active_calls[user_obj.id] = ctx.author.id
        else:
            await ctx.send("Sorry, the chosen user cannot be reached at this time.")
        return

    @commands.command()
    async def hangup(self, ctx):
        if ctx.author.id not in self.calling_users:
            await ctx.send("You're not on a call right now!")
            return

        user_id = self.active_calls[ctx.author.id]
        user_obj = await self.bot.fetch_user(user_id)

        self.calling_users.remove(ctx.author.id)
        self.calling_users.remove(user_id)
        self.active_calls.pop(ctx.author.id)
        self.active_calls.pop(user_id)
        await ctx.send(f"You hung up the call with {user_obj.name}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.active_calls:
            recipient_id = self.active_calls[message.author.id]
            recipient = await self.bot.fetch_user(recipient_id)
            if recipient:
                await recipient.send(f"{message.author.name}: {message.content}")
            else:
                await message.author.send("Sorry, the recipient cannot be reached at this time.")
        elif message.content == "!endcall":
            await self.hangup(message)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command.name == "call":
            self.call_history.append((ctx.author.id, datetime.now()))
            self.call_history = [(u, t) for u, t in self.call_history if datetime.now() - t <= timedelta(seconds=5)]

        elif ctx.command.name == "hangup":
            if ctx.author.id in self.active_calls:
                await self.hangup(ctx)

    async def timeout_call(self, user_id):
        user_obj = await self.bot.fetch_user(user_id)
        self.calling_users.remove(user_id)
        await user_obj.send("Sorry, the call has timed out due to inactivity.")

    async def start_timeout(self, user_id):
        await discord.utils.sleep_until(datetime.now() + timedelta(seconds=30))
        if user_id in self.calling_users:
            await self.timeout_call(user_id)
    
    @commands.command()
    async def endcall(self, ctx):
        if ctx.author.id in self.active_calls:
            await self.hangup(ctx)

   

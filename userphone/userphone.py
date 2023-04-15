import random
import discord
from redbot.core import commands
class UserPhone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.calling_users = set()

    @commands.command()
    async def call(self, ctx):
        if ctx.author.id in self.calling_users:
            await ctx.send("You're already on a call!")
            return

        # Choose a random user who has used the `call` command at that moment
        candidates = [u for u in self.calling_users if u != ctx.author.id]
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

def setup(bot):
    bot.add_cog(UserPhone(bot))

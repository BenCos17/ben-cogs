import discord
from redbot.core import commands

class WordSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is from a bot or from the cog itself to avoid infinite loops
        if message.author.bot or message.author == self.bot.user:
            return

        # Replace 'your_word' with the word you want to search for
        word_to_search = 'your_word'

        # Check if the word is in the message content
        if word_to_search in message.content.lower() and not message.content.startswith(self.bot.command_prefix):
            await message.channel.send(f"Found the word '{word_to_search}' in the message: {message.content}")

    @commands.command(name="wordsearch")
    async def word_search(self, ctx, word: str, limit: int = 100):
        messages = []
        
        # Search the latest messages within the channel
        async for message in ctx.channel.history(limit=limit):
            messages.append(message)
        
        # If the word wasn't found in recent messages, search historical messages in the channel
        async for message in ctx.channel.history(limit=None, oldest_first=True):
            messages.append(message)
            if len(messages) >= limit:
                break
        
        for message in messages:
            if word.lower() in message.content.lower() and not message.content.startswith(self.bot.command_prefix):
                await ctx.send(f"Found the word '{word}' in a message: {message.content}")
                return

        await ctx.send(f"The word '{word}' was not found in the messages.")

def setup(bot):
    bot.add_cog(WordSearch(bot))

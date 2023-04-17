import discord
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

from redbot.core import commands, Config


class ChatBotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            corpus="chatterbot.corpus.english"
        )
        self.chatbot = ChatBot('MyChatBot')
        self.trainer = ChatterBotCorpusTrainer(self.chatbot)
        self.trainer.train(self.config['corpus'])

    @commands.command()
    async def chat(self, ctx, *, message):
        response = self.chatbot.get_response(message)
        await ctx.send(response)


def setup(bot):
    bot.add_cog(ChatBotCog(bot))
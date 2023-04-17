from .chatbot import ChatBotCog


def setup(bot):
    bot.add_cog(ChatBotCog(bot))

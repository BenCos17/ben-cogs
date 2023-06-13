from .linklist import LinkList


def setup(bot):
    bot.add_cog(LinkList(bot))

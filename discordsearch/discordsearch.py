import discord
from redbot.core import commands

class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dsearch(self, ctx, query, *, args=""):
        """Searches for messages in the server.

        Usage: !dsearch <query> [args]

        Args:
        - -u <user>: search for messages by a specific user
        - -c <channel>: search for messages in a specific channel
        - -l <limit>: limit the number of results returned (default: 10)
        """
        channel = ctx.channel
        user = None
        limit = 10

        # Parse the command arguments
        args = args.split()
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "-u":
                i += 1
                user = discord.utils.get(ctx.guild.members, name=args[i])
            elif arg == "-c":
                i += 1
                channel = discord.utils.get(ctx.guild.channels, name=args[i])
            elif arg == "-l":
                i += 1
                limit = int(args[i])
            else:
                await ctx.send(f"Invalid argument: {arg}")
                return
            i += 1

        # Search for messages in the channel
        messages = []
        async for message in channel.history(limit=limit):
            if user and message.author != user:
                continue
            if query.lower() in message.content.lower():
                messages.append(message)

        # Send the search results as embed messages
        if messages:
            for message in messages:
                embed = discord.Embed(title=message.author.display_name, description=message.content, timestamp=message.created_at)
                embed.set_author(name=f"#{message.channel.name}")
                await ctx.send(embed=embed)
        else:
            await ctx.send("No results found.")

def setup(bot):
    bot.add_cog(DiscordSearch(bot))

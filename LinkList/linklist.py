import discord
from redbot.core import commands, Config

class LinkList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # use your own identifier here
        default_global = {"link_links": {}}
        self.config.register_global(**default_global)

    @commands.command()
    async def listlink(self, ctx, link_name: str):
        link_links = await self.config.link_links()
        if link_name not in link_links:
            await ctx.send(f"Invalid link name '{link_name}'. Use !addlink to add a new Nitro link.")
        else:
            await ctx.send(link_links[link_name]["url"])

    @commands.command()
    @commands.is_owner()
    async def addlink(self, ctx, link_name: str, link_url: str):
        await self.config.link_links.set_raw(link_name, value={"url": link_url})
        await ctx.send(f"Added new link '{link_name}': {link_url}")

    @commands.command()
    async def listlinks(self, ctx):
        link_links = await self.config.link_links()
        if not link_links:
            await ctx.send("There are no links configured.")
        else:
            embed = discord.Embed(title="Available  Links", color=discord.Color.blue())
            for name, link in link_links.items():
                embed.add_field(name=name, value=link["url"], inline=False)
            await ctx.send(embed=embed)


    @commands.command()
    @commands.is_owner()
    async def deletelink(self, ctx, link_name: str):
        link_links = await self.config.link_links()
        if link_name not in link_links:
            await ctx.send(f"Invalid link name '{link_name}'.")
        else:
            await self.config.link_links.clear_raw(link_name)
            await ctx.send(f"Removed link '{link_name}'.")

    @commands.command()
    @commands.is_owner()
    async def updatenitro(self, ctx, link_name: str, link_url: str):
        link_links = await self.config.link_links()
        if link_name not in link_links:
            await ctx.send(f"Invalid link name '{link_name}'. Use !addnitro to add a new link.")
        else:
            await self.config.link_links.set_raw(link_name, value={"url": link_url})
            await ctx.send(f"Updated link '{link_name}': {link_url}")

    @commands.command()
    @commands.is_owner()
    async def linkcount(self, ctx):
        link_links = await self.config.link_links()
        if not link_links:
            await ctx.send("There are no Nitro links configured.")
        else:
            counts = {name: 0 for name in link_links.keys()}
            messages = await ctx.channel.history(limit=1000).flatten()
            for message in messages:
                for word in message.content.split():
                    if word in link_links:
                        counts[word] += 1
            count_list = "\n".join([f"{name}: {count}" for name, count in counts.items()])
            await ctx.send(f"Usage counts:\n{count_list}")

import discord
from redbot.core import commands, Config

class LinkList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"link_links": {}, "protected_links": []}
        default_global = {"global_links": {}}
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    async def cog_check(self, ctx):
        # Allow bot owners to use global link commands
        if await self.bot.is_owner(ctx.author):
            return True
        return False

    @commands.command()
    async def listlink(self, ctx, link_name: str):
        guild_link_links = await self.config.guild(ctx.guild).link_links()
        global_link_links = await self.config.global_links()
        if link_name in guild_link_links:
            await ctx.send(guild_link_links[link_name]["url"])
        elif link_name in global_link_links:
            await ctx.send(global_link_links[link_name]["url"])
        else:
            await ctx.send(f"Invalid link name '{link_name}'. Use `!addlink` to add a new link.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def addlink(self, ctx, link_name: str, link_url: str):
        guild_link_links = await self.config.guild(ctx.guild).link_links()
        global_link_links = await self.config.global_links()
        if link_name in guild_link_links or link_name in global_link_links:
            await ctx.send(f"A link with the name '{link_name}' already exists. Use `!updatenitro` to update the link.")
        else:
            await self.config.guild(ctx.guild).link_links.set_raw(link_name, value={"url": link_url})
            await ctx.send(f"Added new guild-specific link '{link_name}': {link_url}")

    @commands.command()
    async def listlinks(self, ctx):
        guild_link_links = await self.config.guild(ctx.guild).link_links()
        global_link_links = await self.config.global_links()
        if not guild_link_links and not global_link_links:
            await ctx.send("There are no links configured.")
        else:
            embed = discord.Embed(title="Available Links", color=discord.Color.blue())
            if guild_link_links:
                for name, link in guild_link_links.items():
                    embed.add_field(name=name, value=link["url"], inline=False)
            if global_link_links:
                for name, link in global_link_links.items():
                    embed.add_field(name=name, value=link["url"], inline=False)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def deletelink(self, ctx, link_name: str):
        guild_link_links = await self.config.guild(ctx.guild).link_links()
        global_link_links = await self.config.global_links()
        protected_links = await self.config.guild(ctx.guild).protected_links()
        if link_name in guild_link_links:
            if link_name in protected_links:
                await ctx.send(f"The guild-specific link '{link_name}' is protected and cannot be deleted.")
            else:
                await self.config.guild(ctx.guild).link_links.clear_raw(link_name)
                await ctx.send(f"Removed guild-specific link '{link_name}'.")
        elif link_name in global_link_links:
            await ctx.send(f"The global link '{link_name}' cannot be deleted.")
        else:
            await ctx.send(f"Invalid link name '{link_name}'.")

    @commands.command()
    @commands.is_owner()
    async def updatenitro(self, ctx, link_name: str, link_url: str):
        guild_link_links = await self.config.guild(ctx.guild).link_links()
        global_link_links = await self.config.global_links()
        if link_name in guild_link_links:
            await self.config.guild(ctx.guild).link_links.set_raw(link_name, value={"url": link_url})
            await ctx.send(f"Updated guild-specific link '{link_name}': {link_url}")
        elif link_name in global_link_links:
            await self.config.global_links.set_raw(link_name, value={"url": link_url})
            await ctx.send(f"Updated global link '{link_name}': {link_url}")
        else:
            await ctx.send(f"Invalid link name '{link_name}'. Use `!addlink` to add a new link.")

    @commands.command()
    @commands.is_owner()
    async def linkcount(self, ctx):
        global_link_links = await self.config.global_links()
        if not global_link_links:
            await ctx.send("There are no global links configured.")
        else:
            counts = {name: 0 for name in global_link_links.keys()}
            messages = await ctx.channel.history(limit=1000).flatten()
            for message in messages:
                for word in message.content.split():
                    if word in global_link_links:
                        counts[word] += 1
            count_list = "\n".join([f"{name}: {count}" for name, count in counts.items()])
            await ctx.send(f"Usage counts:\n{count_list}")

    @commands.command()
    @commands.is_owner()
    async def addgloballink(self, ctx, link_name: str, link_url: str):
        global_link_links = await self.config.global_links()
        if link_name in global_link_links:
            await ctx.send(f"A global link with the name '{link_name}' already exists. Use `!updatenitro` to update the link.")
        else:
            await self.config.global_links.set_raw(link_name, value={"url": link_url})
            await ctx.send(f"Added new global link '{link_name}': {link_url}")

    @commands.command()
    @commands.is_owner()
    async def deletegloballink(self, ctx, link_name: str):
        global_link_links = await self.config.global_links()
        if link_name not in global_link_links:
            await ctx.send(f"Invalid global link name '{link_name}'.")
        else:
            await self.config.global_links.clear_raw(link_name)
            await ctx.send(f"Removed global link '{link_name}'.")

    @commands.command()
    @commands.is_owner()
    async def protectlink(self, ctx, link_name: str):
        protected_links = await self.config.guild(ctx.guild).protected_links()
        guild_link_links = await self.config.guild(ctx.guild).link_links()
        global_link_links = await self.config.global_links()
        if link_name in guild_link_links and link_name not in protected_links:
            protected_links.append(link_name)
            await self.config.guild(ctx.guild).protected_links.set(protected_links)
            await ctx.send(f"The guild-specific link '{link_name}' is now protected and cannot be deleted or edited.")
        elif link_name in global_link_links:
            await ctx.send(f"The global link '{link_name}' cannot be protected.")
        else:
            await ctx.send(f"Invalid link name '{link_name}'.")

    @commands.command()
    @commands.is_owner()
    async def unprotectlink(self, ctx, link_name: str):
        protected_links = await self.config.guild(ctx.guild).protected_links()
        if link_name in protected_links:
            protected_links.remove(link_name)
            await self.config.guild(ctx.guild).protected_links.set(protected_links)
            await ctx.send(f"The guild-specific link '{link_name}' is no longer protected.")
        else:
            await ctx.send(f"The guild-specific link '{link_name}' is not protected.")


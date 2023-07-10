from redbot.core import commands
from redbot.core import Config
from redbot.core.bot import Red

class ServerCooldown(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier

        default_guild_settings = {
            "command_cooldowns": {}
        }
        self.config.register_guild(**default_guild_settings)

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def setcooldown(self, ctx: commands.Context, command_name: str, cooldown_time: int):
        """
        Set the cooldown for a specific command on the server.
        Usage: !setcooldown <command_name> <cooldown_time>
        """
        if not ctx.guild:
            return

        if cooldown_time < 0:
            await ctx.send("Cooldown time cannot be negative.")
            return

        command_name = command_name.lower()
        command_cooldowns = await self.config.guild(ctx.guild).command_cooldowns()

        command_cooldowns[command_name] = cooldown_time
        await self.config.guild(ctx.guild).command_cooldowns.set(command_cooldowns)

        await ctx.send(f"Cooldown for command '{command_name}' set to {cooldown_time} seconds.")

    @commands.command()
    @commands.guild_only()
    async def servercooldown(self, ctx: commands.Context, command_name: str):
        """
        Get the current cooldown for a specific command on the server.
        Usage: !servercooldown <command_name>
        """
        if not ctx.guild:
            return

        command_name = command_name.lower()
        command_cooldowns = await self.config.guild(ctx.guild).command_cooldowns()

        if command_name in command_cooldowns:
            cooldown_time = command_cooldowns[command_name]
            await ctx.send(f"Cooldown for command '{command_name}' is set to {cooldown_time} seconds.")
        else:
            await ctx.send(f"No cooldown set for command '{command_name}'.")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if not ctx.guild:
            return

        command_name = ctx.command.qualified_name.lower()
        command_cooldowns = await self.config.guild(ctx.guild).command_cooldowns()

        if command_name in command_cooldowns:
            cooldown_time = command_cooldowns[command_name]
            await ctx.command.reset_cooldown(ctx)
            ctx.command._buckets._cooldown = commands.Cooldown(rate=1, per=cooldown_time)

def setup(bot: Red):
    bot.add_cog(Cooldown(bot))

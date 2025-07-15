from redbot.core import commands
from redbot.core.bot import Red
import discord
import typing

# Decorator for dashboard pages

def dashboard_page(*args, **kwargs):
    def decorator(func: typing.Callable):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator

class DashboardIntegration:
    bot: Red

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

    @dashboard_page(name=None, description="SkySearch Dashboard Home", methods=("GET",), is_owner=False)
    async def dashboard_home(self, user: discord.User, **kwargs) -> typing.Dict[str, typing.Any]:
        # Basic home page for SkySearch dashboard
        source = '<h2>Welcome to the SkySearch Dashboard Integration!</h2>' \
                 '<p>This page is provided by the SkySearch cog. Use the navigation to explore available features.</p>'
        return {
            "status": 0,
            "web_content": {"source": source},
        }

    @dashboard_page(name="guild", description="View SkySearch info for a guild", methods=("GET",), is_owner=False)
    async def guild_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        # Example guild page
        source = '<h4>SkySearch is active in guild: <b>{{ guild.name }}</b> (ID: {{ guild.id }})</h4>'
        return {
            "status": 0,
            "web_content": {"source": source, "guild": guild},
        } 
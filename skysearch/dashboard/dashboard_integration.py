from redbot.core import commands
import typing
import discord

# Decorator for dashboard pages

def dashboard_page(*args, **kwargs):
    def decorator(func):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator

class DashboardIntegration:
    bot: commands.Bot

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

    @dashboard_page(name=None, description="SkySearch Stats Page", methods=("GET",))
    async def dashboard_stats(self, **kwargs) -> typing.Dict[str, typing.Any]:
        # Example: Show a stats page
        embed_html = (
            '<h2>SkySearch Stats</h2>'
            '<p>This page shows live statistics and data for SkySearch.</p>'
            '<ul>'
            '<li>Aircraft tracked: <b>{{ aircraft_count }}</b></li>'
            '<li>Military ICAO tags: <b>{{ military_count }}</b></li>'
            '<li>Law enforcement ICAO tags: <b>{{ law_count }}</b></li>'
            '</ul>'
        )
        # Try to get stats from the cog if possible
        cog = getattr(self, "_skysearch_cog", None)
        aircraft_count = "?"
        if cog and hasattr(cog, "api"):
            stats = await cog.api.get_stats()
            if stats and "aircraft" in stats:
                aircraft_count = stats["aircraft"]
        if hasattr(cog, "military_icao_set"):
            military_count = len(cog.military_icao_set)
        else:
            military_count = 0
        if hasattr(cog, "law_enforcement_icao_set"):
            law_count = len(cog.law_enforcement_icao_set)
        else:
            law_count = 0
        return {
            "status": 0,
            "web_content": {
                "source": embed_html,
                "aircraft_count": aircraft_count,
                "military_count": military_count,
                "law_count": law_count,
            },
        }

    @dashboard_page(name="guild", description="SkySearch Guild Settings", methods=("GET",))
    async def dashboard_guild_settings(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        # Get the SkySearch cog instance
        cog = getattr(self, "_skysearch_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
        # Fetch guild config
        config = cog.config.guild(guild)
        alert_channel_id = await config.alert_channel()
        alert_role_id = await config.alert_role()
        auto_icao = await config.auto_icao()
        auto_delete = await config.auto_delete_not_found()
        # Resolve channel and role names
        channel_obj = guild.get_channel(alert_channel_id) if alert_channel_id else None
        role_obj = guild.get_role(alert_role_id) if alert_role_id else None
        alert_channel = channel_obj.name if channel_obj else "Not set"
        alert_role = role_obj.name if role_obj else "Not set"
        auto_icao_str = "Enabled" if auto_icao else "Disabled"
        auto_delete_str = "Enabled" if auto_delete else "Disabled"
        html = f'''
            <h2>SkySearch Guild Settings</h2>
            <ul>
                <li><b>Alert Channel:</b> {alert_channel}</li>
                <li><b>Alert Role:</b> {alert_role}</li>
                <li><b>Auto ICAO Lookup:</b> {auto_icao_str}</li>
                <li><b>Auto Delete Not Found:</b> {auto_delete_str}</li>
            </ul>
            <p>Use Discord commands to change these settings.</p>
        '''
        return {
            "status": 0,
            "web_content": {
                "source": html,
            },
        } 
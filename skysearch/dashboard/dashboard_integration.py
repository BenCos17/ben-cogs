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
        #Show a stats page
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

    @dashboard_page(name="guild", description="SkySearch Guild Settings", methods=("GET", "POST"), context_ids=["guild_id"])
    async def dashboard_guild_settings(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        cog = getattr(self, "_skysearch_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
        config = cog.config.guild(guild)
        alert_channel_id = await config.alert_channel()
        alert_role_id = await config.alert_role()
        auto_icao = await config.auto_icao()
        auto_delete = await config.auto_delete_not_found()

        class GuildSettingsForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="skysearch_guild_")
            alert_channel = wtforms.StringField("Alert Channel ID")
            alert_role = wtforms.StringField("Alert Role ID")
            auto_icao = wtforms.BooleanField("Auto ICAO Lookup")
            auto_delete = wtforms.BooleanField("Auto Delete Not Found")
            submit = wtforms.SubmitField("Save Settings")

        form = GuildSettingsForm()
        if not form.is_submitted():
            form.alert_channel.data = str(alert_channel_id or "")
            form.alert_role.data = str(alert_role_id or "")
            form.auto_icao.data = bool(auto_icao)
            form.auto_delete.data = bool(auto_delete)

        if form.validate_on_submit():
            new_channel = int(form.alert_channel.data) if form.alert_channel.data else None
            new_role = int(form.alert_role.data) if form.alert_role.data else None
            await config.alert_channel.set(new_channel)
            await config.alert_role.set(new_role)
            await config.auto_icao.set(form.auto_icao.data)
            await config.auto_delete_not_found.set(form.auto_delete.data)
            return {
                "status": 0,
                "notifications": [{"message": "Settings updated!", "category": "success"}],
                "redirect_url": kwargs["request_url"],
            }

        return {
            "status": 0,
            "web_content": {
                "source": "{{ form|safe }}",
                "form": form,
            },
        } 
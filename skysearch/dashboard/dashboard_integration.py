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
        # Example: Show a simple stats page
        embed_html = (
            '<h2>SkySearch Dashboard</h2>'
            '<p>This is a simple integration page for SkySearch.</p>'
            '<ul>'
            '<li>Aircraft tracked: <b>{{ aircraft_count }}</b></li>'
            '<li>Military ICAO tags: <b>{{ military_count }}</b></li>'
            '<li>Law enforcement ICAO tags: <b>{{ law_count }}</b></li>'
            '</ul>'
        )
        # Try to get stats from the cog if possible
        cog = getattr(self, "_skysearch_cog", None)
        aircraft_count = getattr(cog, "aircraft_commands", None)
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
                "aircraft_count": "?",
                "military_count": military_count,
                "law_count": law_count,
            },
        }

    @dashboard_page(name="guild", description="SkySearch Guild Settings", methods=("GET", "POST"))
    async def dashboard_guild_settings(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        try:
            if "Form" not in kwargs:
                return {"status": 1, "error": "No Form in kwargs"}
            cog = getattr(self, "_skysearch_cog", None)
            if not cog:
                return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
            config = cog.config.guild(guild)
            alert_channel_id = await config.alert_channel()
            alert_role_id = await config.alert_role()
            auto_icao = await config.auto_icao()
            auto_delete = await config.auto_delete_not_found()
            alert_channel = f"<#{alert_channel_id}>" if alert_channel_id else "Not set"
            alert_role = f"<@&{alert_role_id}>" if alert_role_id else "Not set"
            auto_icao_str = "Enabled" if auto_icao else "Disabled"
            auto_delete_str = "Enabled" if auto_delete else "Disabled"

            import wtforms
            class TestForm(kwargs["Form"]):
                test = wtforms.StringField("Test Field")
                submit = wtforms.SubmitField("Submit")
            form = TestForm()
            if form.validate_on_submit():
                return {"status": 0, "notifications": [{"message": "Submitted!", "category": "success"}], "redirect_url": kwargs["request_url"]}
            html = f'''
                <h2>SkySearch Guild Settings</h2>
                <ul>
                    <li><b>Alert Channel:</b> {alert_channel}</li>
                    <li><b>Alert Role:</b> {alert_role}</li>
                    <li><b>Auto ICAO Lookup:</b> {auto_icao_str}</li>
                    <li><b>Auto Delete Not Found:</b> {auto_delete_str}</li>
                </ul>
                <hr/>
                {{% if form %}}{{{{ form|safe }}}}{{% endif %}}
            '''
            return {"status": 0, "web_content": {"source": html, "form": form}}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": 1, "error": f"Exception: {e}"} 
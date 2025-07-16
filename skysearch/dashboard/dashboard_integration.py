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

    @dashboard_page(name="guild", description="SkySearch Guild Settings", methods=("GET",))
    async def dashboard_guild_settings(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        # Check for required dashboard kwargs
        if "Form" not in kwargs or "DpyObjectConverter" not in kwargs:
            return {"status": 1, "error": "Dashboard integration error: Form utilities missing."}
        cog = getattr(self, "_skysearch_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
        config = cog.config.guild(guild)

        import wtforms

        class SettingsForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="skysearch_settings_")
            alert_channel = wtforms.IntegerField(
                "Alert Channel (ID):",
                validators=[wtforms.validators.Optional(), kwargs["DpyObjectConverter"](discord.TextChannel)]
            )
            alert_role = wtforms.IntegerField(
                "Alert Role (ID):",
                validators=[wtforms.validators.Optional(), kwargs["DpyObjectConverter"](discord.Role)]
            )
            auto_icao = wtforms.BooleanField("Auto ICAO Lookup")
            auto_delete = wtforms.BooleanField("Auto Delete Not Found")
            submit = wtforms.SubmitField("Save Settings")

        # Get current values
        alert_channel_id = await config.alert_channel()
        alert_role_id = await config.alert_role()
        auto_icao_val = await config.auto_icao()
        auto_delete_val = await config.auto_delete_not_found()

        form = SettingsForm()
        form.alert_channel.data = alert_channel_id
        form.alert_role.data = alert_role_id
        form.auto_icao.data = auto_icao_val
        form.auto_delete.data = auto_delete_val

        html = "{{ form|safe }}"

        return {
            "status": 0,
            "web_content": {
                "source": html,
                "form": form,
            },
        }
        try:
            cog = getattr(self, "_skysearch_cog", None)
            if not cog:
                return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
            config = cog.config.guild(guild)

            import wtforms

            class SettingsForm(kwargs["Form"]):
                def __init__(self):
                    super().__init__(prefix="skysearch_settings_")
                alert_channel = wtforms.IntegerField(
                    "Alert Channel (ID):",
                    validators=[wtforms.validators.Optional(), kwargs["DpyObjectConverter"](discord.TextChannel)]
                )
                alert_role = wtforms.IntegerField(
                    "Alert Role (ID):",
                    validators=[wtforms.validators.Optional(), kwargs["DpyObjectConverter"](discord.Role)]
                )
                auto_icao = wtforms.BooleanField("Auto ICAO Lookup")
                auto_delete = wtforms.BooleanField("Auto Delete Not Found")
                submit = wtforms.SubmitField("Save Settings")

            # Get current values
            alert_channel_id = await config.alert_channel()
            alert_role_id = await config.alert_role()
            auto_icao_val = await config.auto_icao()
            auto_delete_val = await config.auto_delete_not_found()

            form = SettingsForm()
            if not form.is_submitted():
                form.alert_channel.data = alert_channel_id
                form.alert_role.data = alert_role_id
                form.auto_icao.data = auto_icao_val
                form.auto_delete.data = auto_delete_val

            if form.validate_on_submit() and await form.validate_dpy_converters():
                # Save settings
                await config.alert_channel.set(form.alert_channel.data)
                await config.alert_role.set(form.alert_role.data)
                await config.auto_icao.set(form.auto_icao.data)
                await config.auto_delete_not_found.set(form.auto_delete.data)
                return {
                    "status": 0,
                    "notifications": [{"message": "Settings updated!", "category": "success"}],
                    "redirect_url": kwargs["request_url"],
                }

            html = "{{ form|safe }}"

            return {
                "status": 0,
                "web_content": {
                    "source": html,
                    "form": form,
                },
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": 1, "error": f"Exception: {e}"} 
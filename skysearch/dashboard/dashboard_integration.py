import typing
import discord
import wtforms
from redbot.core import commands

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
        cog = getattr(self, "_skysearch_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
        config = cog.config.guild(guild)
        try:
            alert_channel_id = await config.alert_channel()
            alert_role_id = await config.alert_role()
            auto_icao = await config.auto_icao()
            auto_delete = await config.auto_delete_not_found()
        except Exception as e:
            return {"status": 1, "web_content": {"source": f"<p>Error loading config: {e}</p>"}, "notifications": [{"message": f"Error loading config: {e}", "category": "error"}]}
        # Get channel and role names for display
        alert_channel_name = "None"
        alert_role_name = "None"
        
        if alert_channel_id:
            channel = guild.get_channel(alert_channel_id)
            alert_channel_name = channel.name if channel else f"Unknown Channel ({alert_channel_id})"
        
        if alert_role_id:
            role = guild.get_role(alert_role_id)
            alert_role_name = role.name if role else f"Unknown Role ({alert_role_id})"
        
        # WTForms form definition
        class SettingsForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="settings_")
            alert_channel = wtforms.StringField("Alert Channel ID")
            alert_role = wtforms.StringField("Alert Role ID")
            auto_icao = wtforms.BooleanField("Auto ICAO Lookup")
            auto_delete = wtforms.BooleanField("Auto Delete Not Found")
            submit = wtforms.SubmitField("Save Settings")
        form = SettingsForm()
        form.alert_channel.data = str(alert_channel_id or "")
        form.alert_role.data = str(alert_role_id or "")
        form.auto_icao.data = auto_icao
        form.auto_delete.data = auto_delete
        
        # Check if this is a POST request (form submission)
        if kwargs.get("request_method") == "POST":
            # Verify CSRF token
            post_data = kwargs.get("post_data", {})
            csrf_token = post_data.get("csrf_token")
            expected_csrf = kwargs.get("csrf_token")
            
            if not csrf_token or csrf_token != expected_csrf:
                return {
                    "status": 1,
                    "notifications": [{"message": "Invalid CSRF token. Please try again.", "category": "error"}]
                }
            
            try:
                # Get form data from POST request
                alert_channel_val = int(post_data.get("settings_alert_channel", "")) if post_data.get("settings_alert_channel") else None
                alert_role_val = int(post_data.get("settings_alert_role", "")) if post_data.get("settings_alert_role") else None
                auto_icao_val = "settings_auto_icao" in post_data
                auto_delete_val = "settings_auto_delete" in post_data
                
                # Update config
                await config.alert_channel.set(alert_channel_val)
                await config.alert_role.set(alert_role_val)
                await config.auto_icao.set(auto_icao_val)
                await config.auto_delete_not_found.set(auto_delete_val)
                
                return {
                    "status": 0,
                    "notifications": [{"message": "Settings updated!", "category": "success"}],
                    "redirect_url": kwargs.get("request_url", "")
                }
            except ValueError as e:
                return {
                    "status": 1,
                    "notifications": [{"message": "Invalid channel or role ID. Please enter valid numeric IDs.", "category": "error"}]
                }
            except Exception as e:
                return {
                    "status": 1,
                    "notifications": [{"message": f"Error updating settings: {e}", "category": "error"}]
                }
        # Render the form with channel/role names
        form_html = f"""
        <h2>SkySearch Guild Settings</h2>
        <p>Configure SkySearch settings for this guild.</p>
        
        <div style="margin-bottom: 20px;">
            <h3>Current Settings:</h3>
            <ul>
                <li><strong>Alert Channel:</strong> {alert_channel_name}</li>
                <li><strong>Alert Role:</strong> {alert_role_name}</li>
                <li><strong>Auto ICAO Lookup:</strong> {'Enabled' if auto_icao else 'Disabled'}</li>
                <li><strong>Auto Delete Not Found:</strong> {'Enabled' if auto_delete else 'Disabled'}</li>
            </ul>
        </div>
        
        <h3>Update Settings:</h3>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{kwargs.get('csrf_token', '')}">
            <div style="margin-bottom: 15px;">
                <label for="settings_alert_channel"><strong>Alert Channel ID:</strong></label><br>
                <input type="text" id="settings_alert_channel" name="settings_alert_channel" value="{form.alert_channel.data}" style="width: 300px; padding: 5px;">
                <small>Enter the channel ID where alerts should be sent</small>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label for="settings_alert_role"><strong>Alert Role ID:</strong></label><br>
                <input type="text" id="settings_alert_role" name="settings_alert_role" value="{form.alert_role.data}" style="width: 300px; padding: 5px;">
                <small>Enter the role ID to mention for alerts</small>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label>
                    <input type="checkbox" name="settings_auto_icao" value="y" {"checked" if form.auto_icao.data else ""}>
                    <strong>Auto ICAO Lookup</strong>
                </label>
                <small>Automatically look up ICAO codes when aircraft are mentioned</small>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label>
                    <input type="checkbox" name="settings_auto_delete" value="y" {"checked" if form.auto_delete.data else ""}>
                    <strong>Auto Delete Not Found</strong>
                </label>
                <small>Automatically delete messages when aircraft are not found</small>
            </div>
            
            <button type="submit" style="background: #7289da; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Save Settings</button>
        </form>
        """
        
        return {
            "status": 0,
            "web_content": {"source": form_html},
        } 
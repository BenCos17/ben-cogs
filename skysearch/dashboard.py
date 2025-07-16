import typing
import discord
import wtforms

# Import the dashboard_page decorator from the main cog if needed
try:
    from .skysearch import dashboard_page
except ImportError:
    dashboard_page = None  # Will be injected by setup_dashboard


def setup_dashboard(cog):
    """
    Register dashboard pages for the SkySearch cog.
    This should be called from the cog's __init__ after dashboard is available.
    """
    global dashboard_page
    if dashboard_page is None:
        dashboard_page = getattr(cog, 'dashboard_page', None)
    if dashboard_page is None:
        raise RuntimeError("dashboard_page decorator not found on cog instance!")

    # Register the dashboard pages as methods on the cog
    cog.dashboard_home = dashboard_home.__get__(cog)
    cog.guild_page = guild_page.__get__(cog)
    cog.guild_settings_page = guild_settings_page.__get__(cog)

    # Optionally, register with dashboard_cog if needed (handled by on_dashboard_cog_add)


@dashboard_page(name=None, description="SkySearch Dashboard Home", methods=("GET",), is_owner=False)
async def dashboard_home(self, user: discord.User, **kwargs) -> typing.Dict[str, typing.Any]:
    source = '<h2>Welcome to the SkySearch Dashboard Integration!</h2>' \
             '<p>This page is provided by the SkySearch cog. Use the navigation to explore available features.</p>'
    return {
        "status": 0,
        "web_content": {"source": source},
    }


@dashboard_page(name="guild", description="View SkySearch info for a guild", methods=("GET",), is_owner=False)
async def guild_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
    source = f'<h4>SkySearch is active in guild: <b>{guild.name}</b> (ID: {guild.id})</h4>'
    return {
        "status": 0,
        "web_content": {"source": source},
    }


@dashboard_page(name="settings", description="Configure SkySearch settings for this guild", methods=("GET", "POST"), is_owner=False)
async def guild_settings_page(self, user: discord.User, guild: discord.Guild, request: typing.Optional[dict] = None, **kwargs) -> typing.Dict[str, typing.Any]:
    config = self.config.guild(guild)
    alert_channel = await config.alert_channel()
    alert_role = await config.alert_role()
    auto_icao = await config.auto_icao()
    auto_delete = await config.auto_delete_not_found()

    class SettingsForm(kwargs["Form"]):
        def __init__(self):
            super().__init__(prefix="skysearch_settings_")
        alert_channel: wtforms.StringField = wtforms.StringField("Alert Channel ID", default=str(alert_channel or ""))
        alert_role: wtforms.StringField = wtforms.StringField("Alert Role ID", default=str(alert_role or ""))
        auto_icao: wtforms.BooleanField = wtforms.BooleanField("Auto ICAO Lookup", default=auto_icao)
        auto_delete_not_found: wtforms.BooleanField = wtforms.BooleanField("Auto-Delete 'Not Found' Messages", default=auto_delete)
        submit: wtforms.SubmitField = wtforms.SubmitField("Update Settings")

    form = SettingsForm()
    updates = []
    if form.validate_on_submit():
        try:
            channel_id = form.alert_channel.data.strip()
            if channel_id == "":
                await config.alert_channel.clear()
                updates.append("Alert channel cleared.")
            else:
                await config.alert_channel.set(int(channel_id))
                updates.append(f"Alert channel set to <#{channel_id}>.")
        except Exception as e:
            updates.append(f"Error setting alert channel: {e}")
        try:
            role_id = form.alert_role.data.strip()
            if role_id == "":
                await config.alert_role.clear()
                updates.append("Alert role cleared.")
            else:
                await config.alert_role.set(int(role_id))
                updates.append(f"Alert role set to <@&{role_id}>.")
        except Exception as e:
            updates.append(f"Error setting alert role: {e}")
        try:
            await config.auto_icao.set(bool(form.auto_icao.data))
            updates.append(f"Auto ICAO lookup set to {bool(form.auto_icao.data)}.")
        except Exception as e:
            updates.append(f"Error setting auto ICAO: {e}")
        try:
            await config.auto_delete_not_found.set(bool(form.auto_delete_not_found.data))
            updates.append(f"Auto-delete 'not found' set to {bool(form.auto_delete_not_found.data)}.")
        except Exception as e:
            updates.append(f"Error setting auto-delete: {e}")
    updates_html = f"<div style='color:green;'>{'<br>'.join(updates)}</div>" if updates else ""
    source = f'''
    <h3>SkySearch Guild Settings</h3>
    {updates_html}
    {{ form|safe }}
    '''
    # Permission check: only allow users with Manage Channels permission
    member = guild.get_member(user.id)
    if not member or not member.guild_permissions.manage_channels:
        source = "<h3>Permission Denied</h3><p>You need the <b>Manage Channels</b> permission in this server to access these settings.</p>"
        return {
            "status": 0,
            "web_content": {"source": source},
        }
    return {
        "status": 0,
        "web_content": {"source": source},
    } 
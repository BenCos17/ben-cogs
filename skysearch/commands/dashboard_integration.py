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

class DashboardIntegration(commands.Cog):
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
        # Render the HTML with actual guild data
        source = f'<h4>SkySearch is active in guild: <b>{guild.name}</b> (ID: {guild.id})</h4>'
        return {
            "status": 0,
            "web_content": {"source": source},
        }

    @dashboard_page(name="settings", description="Configure SkySearch settings for this guild", methods=("GET", "POST"), is_owner=False)
    async def guild_settings_page(self, user: discord.User, guild: discord.Guild, request: typing.Optional[dict] = None, **kwargs) -> typing.Dict[str, typing.Any]:
        config = self.bot.get_cog("Skysearch").config.guild(guild)
        # Handle POST (update settings)
        if request and request.get("method") == "POST":
            data = request.get("data", {})
            updates = []
            # Alert Channel
            channel_id = data.get("alert_channel")
            if channel_id is not None:
                try:
                    if channel_id == "":
                        await config.alert_channel.clear()
                        updates.append("Alert channel cleared.")
                    else:
                        await config.alert_channel.set(int(channel_id))
                        updates.append(f"Alert channel set to <#{channel_id}>.")
                except Exception as e:
                    updates.append(f"Error setting alert channel: {e}")
            # Alert Role
            role_id = data.get("alert_role")
            if role_id is not None:
                try:
                    if role_id == "":
                        await config.alert_role.clear()
                        updates.append("Alert role cleared.")
                    else:
                        await config.alert_role.set(int(role_id))
                        updates.append(f"Alert role set to <@&{role_id}>.")
                except Exception as e:
                    updates.append(f"Error setting alert role: {e}")
            # Auto ICAO
            auto_icao = data.get("auto_icao")
            if auto_icao is not None:
                try:
                    await config.auto_icao.set(bool(auto_icao))
                    updates.append(f"Auto ICAO lookup set to {bool(auto_icao)}.")
                except Exception as e:
                    updates.append(f"Error setting auto ICAO: {e}")
            # Auto Delete
            auto_delete = data.get("auto_delete_not_found")
            if auto_delete is not None:
                try:
                    await config.auto_delete_not_found.set(bool(auto_delete))
                    updates.append(f"Auto-delete 'not found' set to {bool(auto_delete)}.")
                except Exception as e:
                    updates.append(f"Error setting auto-delete: {e}")
        # Fetch current settings
        alert_channel = await config.alert_channel()
        alert_role = await config.alert_role()
        auto_icao = await config.auto_icao()
        auto_delete = await config.auto_delete_not_found()
        # Render settings form
        source = f'''
        <h3>SkySearch Guild Settings</h3>
        <form method="post">
            <label>Alert Channel ID:<br><input type="text" name="alert_channel" value="{alert_channel or ''}" placeholder="Channel ID or blank to clear"></label><br>
            <label>Alert Role ID:<br><input type="text" name="alert_role" value="{alert_role or ''}" placeholder="Role ID or blank to clear"></label><br>
            <label>Auto ICAO Lookup:<br><input type="checkbox" name="auto_icao" {'checked' if auto_icao else ''}></label><br>
            <label>Auto-Delete 'Not Found' Messages:<br><input type="checkbox" name="auto_delete_not_found" {'checked' if auto_delete else ''}></label><br>
            <button type="submit">Update Settings</button>
        </form>
        '''
        return {
            "status": 0,
            "web_content": {"source": source},
        } 
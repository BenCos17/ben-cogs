import typing
import discord
import wtforms
from redbot.core import commands
import datetime


def dashboard_page(*args, **kwargs):
    """Decorator for dashboard pages."""
    def decorator(func):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator


class DashboardIntegration:
    """Dashboard integration for Radiosonde cog."""

    bot: commands.Bot

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        """Register dashboard pages when dashboard cog loads."""
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

    @dashboard_page(name=None, description="Radiosonde Stats Page", methods=("GET",))
    async def dashboard_stats(self, **kwargs) -> typing.Dict[str, typing.Any]:
        """Show sonde tracking statistics."""
        cog = getattr(self, "_radiosonde_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>Radiosonde cog not loaded.</p>"}}

        try:
            # Fetch latest sondes to show active tracking
            sondes_data, error = await cog.fetch_sondes()
            total_sondes = len(sondes_data) if sondes_data else 0

            # Count tracked sondes across all guilds
            tracked_total = 0
            guild_count = 0
            for guild in self.bot.guilds:
                tracked = await cog.config.guild(guild).tracked_sondes()
                if tracked:
                    tracked_total += len(tracked)
                    guild_count += 1

            stats_html = f"""
            <div style="background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;">
                <h2 style="color: #ffffff;">📡 Radiosonde Stats</h2>
                <p style="color: #cfcfcf;">Real-time radiosonde tracking statistics from SondeHub V2 API.</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                    <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41; color: #e6e6e6;">
                        <h3 style="color: #ffffff;">📊 API Statistics</h3>
                        <ul style="margin: 0; padding-left: 18px;">
                            <li><strong>Active Sondes:</strong> {total_sondes:,}</li>
                            <li><strong>Sondes Tracked:</strong> {tracked_total}</li>
                            <li><strong>Tracking Guilds:</strong> {guild_count}</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41; color: #e6e6e6;">
                        <h3 style="color: #ffffff;">🌍 API Information</h3>
                        <ul style="margin: 0; padding-left: 18px;">
                            <li><strong>API Host:</strong> api.v2.sondehub.org</li>
                            <li><strong>Status:</strong> {'✅ Online' if not error else '❌ Offline'}</li>
                            <li><strong>Error:</strong> {error if error else 'None'}</li>
                        </ul>
                    </div>
                </div>
            </div>
            """

            return {
                "status": 0,
                "web_content": {
                    "source": stats_html
                }
            }
        except Exception as e:
            return {
                "status": 1,
                "web_content": {
                    "source": f"<p>Error loading statistics: {str(e)}</p>"
                },
                "notifications": [{"message": f"Error loading stats: {str(e)}", "category": "error"}]
            }

    @dashboard_page(name="tracked", description="Tracked Sondes Status", methods=("GET",), context_ids=["guild_id"])
    async def dashboard_tracked_sondes(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        """Show status of tracked sondes for a guild."""
        cog = getattr(self, "_radiosonde_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>Radiosonde cog not loaded.</p>"}}

        try:
            tracked = await cog.config.guild(guild).tracked_sondes()
            if not tracked:
                return {
                    "status": 0,
                    "web_content": {
                        "source": """
                        <div style="background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;">
                            <h2 style="color: #ffffff;">Tracked Sondes</h2>
                            <p style="color: #cfcfcf;">No sondes are currently tracked in this guild.</p>
                        </div>
                        """
                    }
                }

            sondes_data, error = await cog.fetch_sondes()
            if error or not sondes_data:
                return {
                    "status": 1,
                    "web_content": {
                        "source": f"<p>Could not fetch sonde data: {error}</p>"
                    }
                }

            # Build sonde list HTML
            sondes_html = '<div style="background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;">'
            sondes_html += '<h2 style="color: #ffffff;">Tracked Sondes Status</h2>'
            sondes_html += '<div style="margin-top: 20px;">'

            for sonde_id in tracked:
                sonde = sondes_data.get(sonde_id)
                if not sonde:
                    sondes_html += f'''
                    <div style="background-color: #2b2e34; padding: 15px; border-radius: 8px; border: 1px solid #3a3d41; margin-bottom: 15px;">
                        <strong style="color: #ffb3b8;">{sonde_id}</strong>
                        <p style="color: #8a8a8a; margin: 5px 0;">No current data (not in latest API)</p>
                    </div>
                    '''
                else:
                    lat = sonde.get("lat", "—")
                    lon = sonde.get("lon", "—")
                    alt = sonde.get("alt")
                    alt_str = f"{alt:.1f} m" if isinstance(alt, (int, float)) else "—"
                    
                    vel_h = sonde.get("vel_h")
                    vel_v = sonde.get("vel_v")
                    if isinstance(vel_h, (int, float)) and isinstance(vel_v, (int, float)):
                        speed = (vel_h ** 2 + vel_v ** 2) ** 0.5
                    elif isinstance(vel_h, (int, float)):
                        speed = vel_h
                    else:
                        speed = None
                    speed_str = f"{speed:.1f} m/s" if speed is not None else "—"

                    temp = sonde.get("temp", "—")
                    uploader = sonde.get("uploader_callsign") or sonde.get("uploader") or "—"

                    sondes_html += f'''
                    <div style="background-color: #2b2e34; padding: 15px; border-radius: 8px; border: 1px solid #3a3d41; margin-bottom: 15px; border-left: 4px solid #55AAFF;">
                        <strong style="color: #55AAFF;">{sonde_id}</strong>
                        <p style="margin: 8px 0; color: #e6e6e6;">
                            <strong>Position:</strong> {lat}, {lon} | <strong>Altitude:</strong> {alt_str} | <strong>Speed:</strong> {speed_str}<br>
                            <strong>Temp:</strong> {temp}°C | <strong>Uploader:</strong> {uploader}
                        </p>
                    </div>
                    '''

            sondes_html += '</div></div>'
            return {
                "status": 0,
                "web_content": {
                    "source": sondes_html
                }
            }

        except Exception as e:
            return {
                "status": 1,
                "web_content": {
                    "source": f"<p>Error loading tracked sondes: {str(e)}</p>"
                },
                "notifications": [{"message": f"Error: {str(e)}", "category": "error"}]
            }

    @dashboard_page(name="settings", description="Guild Settings", methods=("GET", "POST"), context_ids=["guild_id"])
    async def dashboard_guild_settings(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        """Manage guild-specific radiosonde settings."""
        cog = getattr(self, "_radiosonde_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>Radiosonde cog not loaded.</p>"}}

        config = cog.config.guild(guild)
        try:
            update_channel_id = await config.update_channel()
            update_interval = await config.update_interval()
        except Exception as e:
            return {
                "status": 1,
                "web_content": {"source": f"<p>Error loading config: {e}</p>"},
                "notifications": [{"message": f"Error loading config: {e}", "category": "error"}]
            }

        # Get channel name for display
        update_channel_name = "None"
        if update_channel_id:
            channel = guild.get_channel(update_channel_id)
            update_channel_name = channel.name if channel else f"Unknown Channel ({update_channel_id})"

        # WTForms form definition
        class SettingsForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="settings_")
            update_channel = wtforms.StringField(
                "Update Channel ID",
                render_kw={"class": "form-field", "placeholder": "Leave empty to disable updates"}
            )
            update_interval = wtforms.IntegerField(
                "Update Interval (seconds)",
                render_kw={"class": "form-field", "min": "30", "max": "86400"}
            )
            submit = wtforms.SubmitField("Save Settings", render_kw={"class": "form-submit"})

        settings_form = SettingsForm()
        result_html = ""

        # Handle form submission
        if settings_form.validate_on_submit():
            try:
                channel_val = int(settings_form.update_channel.data) if settings_form.update_channel.data else None
                interval_val = settings_form.update_interval.data or 300

                if interval_val < 30 or interval_val > 86400:
                    result_html = '''
                    <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                        <strong>Error:</strong> Interval must be between 30 seconds and 24 hours (86400 seconds).
                    </div>
                    '''
                elif channel_val and not guild.get_channel(channel_val):
                    result_html = '''
                    <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                        <strong>Error:</strong> Channel not found. Please enter a valid channel ID.
                    </div>
                    '''
                else:
                    await config.update_channel.set(channel_val)
                    await config.update_interval.set(interval_val)

                    if channel_val:
                        channel = guild.get_channel(channel_val)
                        update_channel_name = channel.name if channel else f"Channel {channel_val}"
                    else:
                        update_channel_name = "None"

                    result_html = '''
                    <div style="margin-top: 20px; padding: 10px; background-color: #152b15; border: 1px solid #245a24; border-radius: 4px; color: #b8ffb8;">
                        <strong>Success:</strong> Settings updated successfully!
                    </div>
                    '''
            except ValueError:
                result_html = '''
                <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                    <strong>Error:</strong> Invalid channel ID. Please enter a valid numeric ID.
                </div>
                '''
            except Exception as e:
                result_html = f'''
                <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                    <strong>Error:</strong> {str(e)}
                </div>
                '''

        # Populate form
        settings_form.update_channel.data = str(update_channel_id or "")
        settings_form.update_interval.data = update_interval

        return {
            "status": 0,
            "web_content": {
                "source": """
                <div style="background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;">
                    <h2 style="color: #ffffff;">Radiosonde Guild Settings</h2>
                    <p style="color: #cfcfcf;">Configure sonde update settings for this guild.</p>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #ffffff;">Current Settings:</h3>
                        <div style="background-color: #2b2e34; padding: 15px; border-radius: 8px; border: 1px solid #3a3d41;">
                            <ul style="margin: 0; padding-left: 20px;">
                                <li><strong>Update Channel:</strong> {{ update_channel_name }}</li>
                                <li><strong>Update Interval:</strong> {{ update_interval }} seconds</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #ffffff;">Update Settings:</h3>
                        <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41;">
                            <style>
                                .form-field {
                                    background-color: #1e1f22;
                                    border: 1px solid #3a3d41;
                                    border-radius: 4px;
                                    color: #e6e6e6;
                                    padding: 8px 12px;
                                    font-size: 14px;
                                    margin-bottom: 12px;
                                    width: 100%;
                                }
                                .form-field:focus {
                                    outline: none;
                                    border-color: #5865f2;
                                    box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
                                }
                                .form-submit {
                                    background-color: #5865f2;
                                    border: none;
                                    border-radius: 4px;
                                    color: #ffffff;
                                    padding: 10px 20px;
                                    font-size: 14px;
                                    font-weight: bold;
                                    cursor: pointer;
                                    transition: background-color 0.2s;
                                }
                                .form-submit:hover {
                                    background-color: #4752c4;
                                }
                            </style>
                            <div style="display: flex; flex-direction: column; gap: 15px;">
                                {{ settings_form|safe }}
                            </div>
                        </div>
                    </div>
                    
                    {{ result_html|safe }}
                </div>
                """,
                "settings_form": settings_form,
                "result_html": result_html,
                "update_channel_name": update_channel_name,
                "update_interval": update_interval,
            },
        }

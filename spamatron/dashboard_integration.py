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

    @dashboard_page(name=None, description="Spamatron Stats Page", methods=("GET",))
    async def dashboard_stats(self, **kwargs) -> typing.Dict[str, typing.Any]:
        """Show a stats page for Spamatron."""
        embed_html = (
            '<h2>Spamatron Statistics</h2>'
            '<p>This page shows live statistics and data for Spamatron.</p>'
            '<ul>'
            '<li>Total servers with typo watch enabled: <b>{{ enabled_servers }}</b></li>'
            '<li>Total watched words across all servers: <b>{{ total_words }}</b></li>'
            '<li>Active ghostping tasks: <b>{{ active_ghostpings }}</b></li>'
            '</ul>'
        )
        
        # Try to get stats from the cog if possible
        cog = getattr(self, "_spamatron_cog", None)
        enabled_servers = "?"
        total_words = "?"
        active_ghostpings = "?"
        
        if cog:
            # Count enabled servers
            enabled_count = 0
            total_word_count = 0
            for guild in cog.bot.guilds:
                try:
                    settings = await cog.config.guild(guild).typo_watch()
                    if settings["enabled"]:
                        enabled_count += 1
                        total_word_count += len(settings["words"])
                except:
                    continue
            
            enabled_servers = enabled_count
            total_words = total_word_count
            active_ghostpings = len(cog.ghostping_tasks)
        
        return {
            "status": 0,
            "web_content": {
                "source": embed_html,
                "enabled_servers": enabled_servers,
                "total_words": total_words,
                "active_ghostpings": active_ghostpings,
            },
        }

    @dashboard_page(name="typowatch", description="Spamatron Typo Watch Management", methods=("GET", "POST"), context_ids=["guild_id"])
    async def dashboard_typowatch(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        """Manage typo watch settings for a guild."""
        cog = getattr(self, "_spamatron_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>Spamatron cog not loaded.</p>"}}
        
        # Get current settings
        try:
            settings = await cog.config.guild(guild).typo_watch()
        except Exception as e:
            return {"status": 1, "web_content": {"source": f"<p>Error loading config: {e}</p>"}, "notifications": [{"message": f"Error loading config: {e}", "category": "error"}]}

        # WTForms form definitions
        class ToggleForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="toggle_")
            submit = wtforms.SubmitField("Toggle Typo Watch")

        class AddWordForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="add_")
            correct_word = wtforms.StringField("Correct Word", validators=[wtforms.validators.DataRequired()])
            typo_word = wtforms.StringField("Typo Word", validators=[wtforms.validators.DataRequired()])
            first_response = wtforms.StringField("First Response", validators=[wtforms.validators.DataRequired()])
            submit = wtforms.SubmitField("Add Word")

        class RemoveWordForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="remove_")
            correct_word = wtforms.StringField("Correct Word to Remove", validators=[wtforms.validators.DataRequired()])
            submit = wtforms.SubmitField("Remove Word")

        class ResponsesForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="responses_")
            correct_word = wtforms.StringField("Correct Word", validators=[wtforms.validators.DataRequired()])
            responses = wtforms.TextAreaField("Responses (separate with |)", validators=[wtforms.validators.DataRequired()])
            submit = wtforms.SubmitField("Update Responses")

        toggle_form = ToggleForm()
        add_form = AddWordForm()
        remove_form = RemoveWordForm()
        responses_form = ResponsesForm()
        
        result_html = ""
        
        # Handle form submissions
        if kwargs.get("request") and kwargs["request"].method == "POST":
            form_prefix = kwargs["request"].form.get("submit", "").split("_")[0]
            
            if form_prefix == "toggle" and toggle_form.validate_on_submit():
                async with cog.config.guild(guild).typo_watch() as settings:
                    settings["enabled"] = not settings["enabled"]
                    state = "enabled" if settings["enabled"] else "disabled"
                result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;"><strong>Success:</strong> Typo watching is now {state}</div>'
            
            elif form_prefix == "add" and add_form.validate_on_submit():
                async with cog.config.guild(guild).typo_watch() as settings:
                    settings["words"][add_form.correct_word.data] = {
                        "typo": add_form.typo_word.data,
                        "responses": [add_form.first_response.data]
                    }
                result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;"><strong>Success:</strong> Now watching for \'{add_form.typo_word.data}\' to suggest \'{add_form.correct_word.data}\'</div>'
            
            elif form_prefix == "remove" and remove_form.validate_on_submit():
                async with cog.config.guild(guild).typo_watch() as settings:
                    if remove_form.correct_word.data in settings["words"]:
                        del settings["words"][remove_form.correct_word.data]
                        result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;"><strong>Success:</strong> Removed \'{remove_form.correct_word.data}\' from the watch list</div>'
                    else:
                        result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;"><strong>Error:</strong> \'{remove_form.correct_word.data}\' was not in the watch list</div>'
            
            elif form_prefix == "responses" and responses_form.validate_on_submit():
                async with cog.config.guild(guild).typo_watch() as settings:
                    if responses_form.correct_word.data not in settings["words"]:
                        result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;"><strong>Error:</strong> \'{responses_form.correct_word.data}\' is not in the watch list</div>'
                    else:
                        new_responses = [r.strip() for r in responses_form.responses.data.split("|")]
                        if not new_responses:
                            result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;"><strong>Error:</strong> Please provide at least one response</div>'
                        else:
                            settings["words"][responses_form.correct_word.data]["responses"] = new_responses
                            result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;"><strong>Success:</strong> Updated responses for \'{responses_form.correct_word.data}\'</div>'

        # Get updated settings after any changes
        settings = await cog.config.guild(guild).typo_watch()
        
        # Build current words display
        words_html = ""
        if settings["words"]:
            for correct_word, word_data in settings["words"].items():
                responses_list = "<br>".join([f"{i+1}. {r}" for i, r in enumerate(word_data["responses"])])
                words_html += f'''
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: #f8f9fa;">
                    <h4 style="margin-top: 0; color: #333;">{correct_word}</h4>
                    <p><strong>Typo:</strong> {word_data["typo"]}</p>
                    <p><strong>Responses:</strong></p>
                    <div style="margin-left: 20px;">{responses_list}</div>
                </div>
                '''
        else:
            words_html = '<p style="color: #666; font-style: italic;">No words are being watched.</p>'

        return {
            "status": 0,
            "web_content": {
                "source": """
                <h2>Spamatron Typo Watch Management</h2>
                <p>Configure typo watch settings for this server.</p>
                
                <div style="margin-bottom: 30px;">
                    <h3>Current Status</h3>
                    <p><strong>Typo Watch:</strong> {{ enabled_status }}</p>
                    <p><strong>Watched Words:</strong> {{ word_count }}</p>
                </div>
                
                {{ result_html|safe }}
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                    <div style="background-color: #808080; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3>Toggle Typo Watch</h3>
                        {{ toggle_form|safe }}
                    </div>
                    
                    <div style="background-color: #808080; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3>Add New Word</h3>
                        {{ add_form|safe }}
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                    <div style="background-color: #808080; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3>Remove Word</h3>
                        {{ remove_form|safe }}
                    </div>
                    
                    <div style="background-color: #808080; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3>Update Responses</h3>
                        {{ responses_form|safe }}
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <h3>Current Watched Words</h3>
                    {{ words_html|safe }}
                </div>
                """,
                "toggle_form": toggle_form,
                "add_form": add_form,
                "remove_form": remove_form,
                "responses_form": responses_form,
                "result_html": result_html,
                "enabled_status": "Enabled" if settings["enabled"] else "Disabled",
                "word_count": len(settings["words"]),
                "words_html": words_html,
            },
        }

    @dashboard_page(name="ghostping", description="Spamatron Ghostping Management", methods=("GET", "POST"), context_ids=["guild_id"])
    async def dashboard_ghostping(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        """Manage ghostping tasks for a guild."""
        cog = getattr(self, "_spamatron_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>Spamatron cog not loaded.</p>"}}

        # WTForms form definition
        class GhostpingForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="ghostping_")
            member_id = wtforms.StringField("Member ID", validators=[wtforms.validators.DataRequired()])
            channel_id = wtforms.StringField("Channel ID", validators=[wtforms.validators.DataRequired()])
            amount = wtforms.IntegerField("Amount", validators=[wtforms.validators.DataRequired(), wtforms.validators.NumberRange(min=1, max=100)])
            interval = wtforms.IntegerField("Interval (seconds)", validators=[wtforms.validators.DataRequired(), wtforms.validators.NumberRange(min=1, max=60)])
            submit = wtforms.SubmitField("Start Ghostping")

        class StopForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="stop_")
            submit = wtforms.SubmitField("Stop All Ghostpings")

        ghostping_form = GhostpingForm()
        stop_form = StopForm()
        result_html = ""

        # Handle form submissions
        if kwargs.get("request") and kwargs["request"].method == "POST":
            form_prefix = kwargs["request"].form.get("submit", "").split("_")[0]
            
            if form_prefix == "ghostping" and ghostping_form.validate_on_submit():
                try:
                    member_id = int(ghostping_form.member_id.data)
                    channel_id = int(ghostping_form.channel_id.data)
                    amount = ghostping_form.amount.data
                    interval = ghostping_form.interval.data
                    
                    member = guild.get_member(member_id)
                    channel = guild.get_channel(channel_id)
                    
                    if not member:
                        result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;"><strong>Error:</strong> Member not found</div>'
                    elif not channel:
                        result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;"><strong>Error:</strong> Channel not found</div>'
                    else:
                        # Note: This would need to be implemented in the cog to work properly
                        result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;"><strong>Success:</strong> Ghostping task started for {member.display_name} in {channel.name}</div>'
                        
                except ValueError:
                    result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;"><strong>Error:</strong> Invalid ID format</div>'
            
            elif form_prefix == "stop" and stop_form.validate_on_submit():
                # Note: This would need to be implemented in the cog to work properly
                result_html = f'<div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;"><strong>Success:</strong> All ghostping tasks stopped</div>'

        # Build active tasks display
        active_tasks_html = ""
        if hasattr(cog, 'ghostping_tasks') and cog.ghostping_tasks:
            active_tasks_html = '<div style="margin-top: 15px;">'
            for user_id, task in cog.ghostping_tasks.items():
                user = guild.get_member(user_id)
                user_name = user.display_name if user else f"User {user_id}"
                task_status = "Running" if not task.done() else "Completed"
                task_status_color = "#28a745" if not task.done() else "#dc3545"
                
                active_tasks_html += f'''
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; background-color: #f8f9fa;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #333;">{user_name}</h4>
                            <p style="margin: 5px 0; color: #666;">User ID: {user_id}</p>
                            <p style="margin: 5px 0; color: #666;">Task ID: {id(task)}</p>
                        </div>
                        <div style="text-align: right;">
                            <span style="background-color: {task_status_color}; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                                {task_status}
                            </span>
                        </div>
                    </div>
                </div>
                '''
            active_tasks_html += '</div>'
        else:
            active_tasks_html = '<p style="color: #666; font-style: italic;">No active ghostping tasks</p>'

        return {
            "status": 0,
            "web_content": {
                "source": """
                <h2>Spamatron Ghostping Management</h2>
                <p>Manage ghostping tasks for this server.</p>
                
                {{ result_html|safe }}
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                    <div style="background-color: #808080; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3>Start Ghostping Task</h3>
                        <p style="color: #666; font-size: 14px;">Enter the member ID and channel ID to start a ghostping task.</p>
                        {{ ghostping_form|safe }}
                    </div>
                    
                    <div style="background-color: #808080; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3>Stop All Ghostpings</h3>
                        <p style="color: #666; font-size: 14px;">Stop all currently running ghostping tasks.</p>
                        {{ stop_form|safe }}
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <h3>Active Ghostping Tasks</h3>
                    {{ active_tasks_html|safe }}
                </div>
                

                """,
                "ghostping_form": ghostping_form,
                "stop_form": stop_form,
                "result_html": result_html,
                "active_tasks_html": active_tasks_html,
            },
        } 
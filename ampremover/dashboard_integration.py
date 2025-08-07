from redbot.core import commands
from redbot.core.bot import Red
import discord
import typing
import aiohttp
import asyncio
import re

def dashboard_page(*args, **kwargs):
    """This decorator is required because the cog Dashboard may load after the third party when the bot is started."""
    def decorator(func: typing.Callable):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator


class DashboardIntegration:
    bot: Red

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        """on_dashboard_cog_add is triggered by the Dashboard cog automatically."""
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)  # Add the third party to Dashboard.

    @dashboard_page(name=None, description="Convert AMP URLs to canonical URLs!", methods=("GET", "POST"))
    async def convert_amp_dashboard(self, user: discord.User, **kwargs) -> typing.Dict[str, typing.Any]:
        """Dashboard page for converting AMP URLs to canonical URLs."""
        import wtforms
        
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="convert_amp_form_")
            url: wtforms.TextAreaField = wtforms.TextAreaField(
                "URL(s) to convert:", 
                validators=[wtforms.validators.InputRequired(), wtforms.validators.URL()],
                description="Enter one or more AMP URLs to convert to canonical URLs"
            )
            submit: wtforms.SubmitField = wtforms.SubmitField("Convert URLs!")

        form: Form = Form()
        
        if form.validate_on_submit():
            urls = self.extract_urls(form.url.data)
            if urls:
                canonical_links = await self.fetch_canonical_links(urls)
                if canonical_links:
                    result_html = f"""
                    <div class="alert alert-success">
                        <h4>✅ Conversion Successful!</h4>
                        <p><strong>Original URLs:</strong></p>
                        <ul>
                            {''.join(f'<li><code>{url}</code></li>' for url in urls)}
                        </ul>
                        <p><strong>Canonical URLs:</strong></p>
                        <ul>
                            {''.join(f'<li><a href="{link}" target="_blank">{link}</a></li>' for link in canonical_links)}
                        </ul>
                    </div>
                    """
                    return {
                        "status": 0,
                        "notifications": [{"message": f"Successfully converted {len(canonical_links)} URL(s)!", "category": "success"}],
                        "web_content": {"source": result_html}
                    }
                else:
                    return {
                        "status": 0,
                        "notifications": [{"message": "No canonical URLs found for the provided URLs.", "category": "warning"}],
                        "web_content": {"source": "{{ form|safe }}", "form": form}
                    }
            else:
                return {
                    "status": 0,
                    "notifications": [{"message": "No valid URLs found in the input.", "category": "error"}],
                    "web_content": {"source": "{{ form|safe }}", "form": form}
                }

        source = """
        <div class="container">
            <h2>🔗 AMP URL Converter</h2>
            <p>Convert AMP (Accelerated Mobile Pages) URLs to their canonical forms using the AmputatorBot API.</p>
            <div class="card">
                <div class="card-body">
                    {{ form|safe }}
                </div>
            </div>
            <div class="mt-3">
                <h5>How it works:</h5>
                <ul>
                    <li>Enter one or more AMP URLs in the text area above</li>
                    <li>Click "Convert URLs!" to process them</li>
                    <li>The system will return the canonical (non-AMP) versions</li>
                </ul>
                <div class="alert alert-info">
                    <strong>Example:</strong> <code>https://www.google.com/amp/s/example.com/article</code> → <code>https://example.com/article</code>
                </div>
            </div>
        </div>
        """

        return {
            "status": 0,
            "web_content": {"source": source, "form": form}
        }

    @dashboard_page(name="settings", description="Configure AMP URL conversion settings for this guild", methods=("GET", "POST"))
    async def settings_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        """Dashboard page for managing guild settings."""
        import wtforms
        
        # Get current settings
        opted_in = await self.config.guild(guild).opted_in()
        
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="settings_form_")
            auto_convert: wtforms.BooleanField = wtforms.BooleanField(
                "Enable automatic AMP URL conversion", 
                default=opted_in,
                description="When enabled, the bot will automatically convert AMP URLs in messages"
            )
            submit: wtforms.SubmitField = wtforms.SubmitField("Save Settings!")

        form: Form = Form()
        
        if form.validate_on_submit():
            new_setting = form.auto_convert.data
            await self.config.guild(guild).opted_in.set(new_setting)
            
            status_text = "enabled" if new_setting else "disabled"
            return {
                "status": 0,
                "notifications": [{"message": f"Automatic AMP URL conversion {status_text} for {guild.name}!", "category": "success"}],
                "web_content": {"source": "{{ form|safe }}", "form": form}
            }

        source = f"""
        <div class="container">
            <h2>⚙️ AMP Remover Settings</h2>
            <p>Configure AMP URL conversion settings for <strong>{guild.name}</strong>.</p>
            
            <div class="card">
                <div class="card-header">
                    <h5>Current Status</h5>
                </div>
                <div class="card-body">
                    <p><strong>Automatic Conversion:</strong> 
                        <span class="badge badge-{'success' if opted_in else 'danger'}">
                            {'Enabled' if opted_in else 'Disabled'}
                        </span>
                    </p>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h5>Settings</h5>
                </div>
                <div class="card-body">
                    {{ form|safe }}
                </div>
            </div>
            
            <div class="mt-3">
                <h5>What these settings do:</h5>
                <ul>
                    <li><strong>Automatic Conversion:</strong> When enabled, the bot will automatically detect AMP URLs in messages and respond with canonical versions</li>
                    <li>Users can still use the <code>[p]amputator convert</code> command regardless of this setting</li>
                    <li>This setting only affects automatic detection in messages</li>
                </ul>
            </div>
        </div>
        """

        return {
            "status": 0,
            "web_content": {"source": source, "form": form}
        }

    @dashboard_page(name="stats", description="View AMP URL conversion statistics", methods=("GET",))
    async def stats_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        """Dashboard page for viewing conversion statistics."""
        # Get guild settings
        opted_in = await self.config.guild(guild).opted_in()
        
        # For now, we'll show basic stats. You can expand this later with actual conversion tracking
        stats_html = f"""
        <div class="container">
            <h2>📊 AMP Remover Statistics</h2>
            <p>Statistics for <strong>{guild.name}</strong></p>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Guild Settings</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Automatic Conversion:</strong> 
                                <span class="badge badge-{'success' if opted_in else 'danger'}">
                                    {'Enabled' if opted_in else 'Disabled'}
                                </span>
                            </p>
                            <p><strong>Guild ID:</strong> <code>{guild.id}</code></p>
                            <p><strong>Member Count:</strong> {guild.member_count:,}</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Bot Information</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Bot Name:</strong> {self.bot.user.display_name}</p>
                            <p><strong>API Used:</strong> AmputatorBot API</p>
                            <p><strong>Commands Available:</strong></p>
                            <ul>
                                <li><code>[p]amputator convert</code> - Manual conversion</li>
                                <li><code>[p]amputator optin</code> - Enable auto-conversion</li>
                                <li><code>[p]amputator optout</code> - Disable auto-conversion</li>
                                <li><code>[p]amputator settings</code> - View settings</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-3">
                <div class="alert alert-info">
                    <h5>💡 Tip</h5>
                    <p>To track conversion statistics, you would need to add logging functionality to the main cog. 
                    This could include tracking the number of URLs converted, success rates, and user activity.</p>
                </div>
            </div>
        </div>
        """

        return {
            "status": 0,
            "web_content": {"source": stats_html}
        }

    def extract_urls(self, message: str):
        """Extract URLs from a given message using regex."""
        return re.findall(r'(https?://\S+)', message)

    async def fetch_canonical_links(self, urls):
        """Fetch canonical links for a list of URLs using the AmputatorBot API."""
        canonical_links = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                api_url = f"https://www.amputatorbot.com/api/v1/convert?gac=true&md=3&q={url}"
                try:
                    async with session.get(api_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if not 'error' in data:
                                links = [link['canonical']['url'] for link in data if link['canonical']]
                                canonical_links.extend(links)
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    continue
        return canonical_links 
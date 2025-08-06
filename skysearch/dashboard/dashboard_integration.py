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

    @dashboard_page(name="lookup", description="SkySearch Aircraft Lookup", methods=("GET", "POST"))
    async def dashboard_aircraft_lookup(self, **kwargs) -> typing.Dict[str, typing.Any]:
        cog = getattr(self, "_skysearch_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
        
        # WTForms form definition
        class LookupForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="lookup_")
            search_type = wtforms.SelectField("Search Type", choices=[
                ("icao", "ICAO Hex Code"),
                ("callsign", "Flight Callsign"),
                ("reg", "Registration"),
                ("type", "Aircraft Type")
            ])
            search_value = wtforms.StringField("Search Value")
            submit = wtforms.SubmitField("Search Aircraft")
        
        form = LookupForm()
        result_html = ""
        
        # Handle form submission using WTForms validation
        if form.validate_on_submit():
            try:
                search_type = form.search_type.data
                search_value = form.search_value.data.strip()
                
                if not search_value:
                    return {
                        "status": 1,
                        "notifications": [{"message": "Please enter a search value.", "category": "error"}],
                        "web_content": {
                            "source": """
                            <h2>SkySearch Aircraft Lookup</h2>
                            <p>Search for aircraft by ICAO code, callsign, registration, or aircraft type.</p>
                            
                            <div style="margin-bottom: 20px;">
                                <h3>Search Aircraft:</h3>
                                {{ form|safe }}
                            </div>
                            """,
                            "form": form,
                        }
                    }
                
                # Build the API URL based on search type
                api_url = await cog.api.get_api_url()
                if search_type == "icao":
                    url = f"{api_url}/?find_hex={search_value}"
                elif search_type == "callsign":
                    url = f"{api_url}/?find_callsign={search_value}"
                elif search_type == "reg":
                    url = f"{api_url}/?find_reg={search_value}"
                elif search_type == "type":
                    url = f"{api_url}/?find_type={search_value}"
                else:
                    return {
                        "status": 1,
                        "notifications": [{"message": "Invalid search type.", "category": "error"}],
                        "web_content": {
                            "source": """
                            <h2>SkySearch Aircraft Lookup</h2>
                            <p>Search for aircraft by ICAO code, callsign, registration, or aircraft type.</p>
                            
                            <div style="margin-bottom: 20px;">
                                <h3>Search Aircraft:</h3>
                                {{ form|safe }}
                            </div>
                            """,
                            "form": form,
                        }
                    }
                
                # Make the API request
                response = await cog.api.make_request(url)
                
                if response:
                    # Support both 'aircraft' and 'ac' keys
                    aircraft_list = response.get('aircraft') or response.get('ac')
                    
                    if aircraft_list and len(aircraft_list) > 0:
                        result_html = '<div style="margin-top: 20px;"><h3>Search Results:</h3>'
                        
                        for i, aircraft_data in enumerate(aircraft_list[:5]):  # Limit to 5 results
                            # Get photo for the aircraft
                            icao = aircraft_data.get('hex', '')
                            if icao:
                                icao = icao.upper()
                            image_url, photographer = await cog.helpers.get_photo_by_hex(icao)
                            
                            # Create aircraft info HTML
                            description = f"{aircraft_data.get('desc', 'N/A')}"
                            if aircraft_data.get('year', None) is not None:
                                description += f" ({aircraft_data.get('year')})"
                            
                            callsign = aircraft_data.get('flight', 'N/A').strip()
                            if not callsign or callsign == 'N/A':
                                callsign = 'BLOCKED'
                            
                            registration = aircraft_data.get('reg', 'N/A')
                            if registration and registration != 'N/A':
                                registration = registration.upper()
                            
                            altitude = aircraft_data.get('alt_baro', 'N/A')
                            if altitude == 'ground':
                                altitude_text = "On ground"
                            elif altitude != 'N/A':
                                if isinstance(altitude, int):
                                    altitude = "{:,}".format(altitude)
                                altitude_text = f"{altitude} ft"
                            else:
                                altitude_text = "N/A"
                            
                            lat = aircraft_data.get('lat', 'N/A')
                            lon = aircraft_data.get('lon', 'N/A')
                            if lat != 'N/A' and lat is not None and lon != 'N/A' and lon is not None:
                                try:
                                    lat_rounded = round(float(lat), 2)
                                    lon_rounded = round(float(lon), 2)
                                    lat_dir = "N" if lat_rounded >= 0 else "S"
                                    lon_dir = "E" if lon_rounded >= 0 else "W"
                                    position_text = f"{abs(lat_rounded)}{lat_dir}, {abs(lon_rounded)}{lon_dir}"
                                except:
                                    position_text = "N/A"
                            else:
                                position_text = "N/A"
                            
                            squawk_code = aircraft_data.get('squawk', 'N/A')
                            emergency_squawk_codes = ['7500', '7600', '7700']
                            if squawk_code in emergency_squawk_codes:
                                squawk_style = 'color: red; font-weight: bold;'
                            else:
                                squawk_style = ''
                            
                            globe_link = f"https://globe.airplanes.live/?icao={icao}"
                            
                            result_html += f'''
                            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: #f9f9f9;">
                                <h4 style="margin-top: 0; color: #333;">{description}</h4>
                                <div style="display: flex; gap: 20px;">
                                    <div style="flex: 1;">
                                        <p><strong>Callsign:</strong> {callsign}</p>
                                        <p><strong>Registration:</strong> {registration}</p>
                                        <p><strong>ICAO:</strong> {icao}</p>
                                        <p><strong>Altitude:</strong> {altitude_text}</p>
                                        <p><strong>Position:</strong> {position_text}</p>
                                        <p><strong>Squawk:</strong> <span style="{squawk_style}">{squawk_code}</span></p>
                                    </div>
                                    <div style="flex: 0 0 200px;">
                                        {f'<img src="{image_url}" alt="Aircraft photo" style="max-width: 100%; height: auto; border-radius: 4px;">' if image_url else '<p style="color: #666; font-style: italic;">No photo available</p>'}
                                        {f'<p style="font-size: 12px; color: #666; margin-top: 5px;">Photo by: {photographer}</p>' if photographer else ''}
                                    </div>
                                </div>
                                <div style="margin-top: 10px;">
                                    <a href="{globe_link}" target="_blank" style="background-color: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">View on Globe</a>
                                </div>
                            </div>
                            '''
                        
                        if len(aircraft_list) > 5:
                            result_html += f'<p style="color: #666; font-style: italic;">Showing first 5 of {len(aircraft_list)} results</p>'
                        
                        result_html += '</div>'
                    else:
                        result_html = '''
                        <div style="margin-top: 20px;">
                            <h3>No Results Found</h3>
                            <p style="color: #666;">No aircraft found matching your search criteria. Please try a different search term.</p>
                        </div>
                        '''
                else:
                    result_html = '''
                    <div style="margin-top: 20px;">
                        <h3>Error</h3>
                        <p style="color: #666;">Unable to retrieve aircraft information. Please check your search terms and try again.</p>
                    </div>
                    '''
                    
            except Exception as e:
                result_html = f'''
                <div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;">
                    <strong>Error:</strong> An error occurred while searching: {str(e)}
                </div>
                '''
        
        # Populate form with current values if this was a POST request
        if kwargs.get("request") and kwargs["request"].method == "POST":
            form.search_type.data = kwargs["request"].form.get("search_type", "icao")
            form.search_value.data = kwargs["request"].form.get("search_value", "")
        
        return {
            "status": 0,
            "web_content": {
                "source": f"""
                <h2>SkySearch Aircraft Lookup</h2>
                <p>Search for aircraft by ICAO code, callsign, registration, or aircraft type.</p>
                
                <div style="margin-bottom: 20px;">
                    <h3>Search Aircraft:</h3>
                    {{ form|safe }}
                </div>
                
                {result_html}
                """,
                "form": form,
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
        
        # Handle form submission using WTForms validation
        if form.validate_on_submit():
            try:
                # Validate and update config
                alert_channel_val = int(form.alert_channel.data) if form.alert_channel.data else None
                alert_role_val = int(form.alert_role.data) if form.alert_role.data else None
                
                await config.alert_channel.set(alert_channel_val)
                await config.alert_role.set(alert_role_val)
                await config.auto_icao.set(form.auto_icao.data)
                await config.auto_delete_not_found.set(form.auto_delete.data)
                
                # Update the display values to reflect the new settings
                if alert_channel_val:
                    channel = guild.get_channel(alert_channel_val)
                    alert_channel_name = channel.name if channel else f"Unknown Channel ({alert_channel_val})"
                else:
                    alert_channel_name = "None"
                    
                if alert_role_val:
                    role = guild.get_role(alert_role_val)
                    alert_role_name = role.name if role else f"Unknown Role ({alert_role_val})"
                else:
                    alert_role_name = "None"
                
                return {
                    "status": 0,
                    "notifications": [{"message": "Settings updated!", "category": "success"}],
                    "web_content": {
                        "source": """
                        <h2>SkySearch Guild Settings</h2>
                        <p>Configure SkySearch settings for this guild.</p>
                        
                        <div style="margin-bottom: 20px;">
                            <h3>Current Settings:</h3>
                            <ul>
                                <li><strong>Alert Channel:</strong> {{ alert_channel_name }}</li>
                                <li><strong>Alert Role:</strong> {{ alert_role_name }}</li>
                                <li><strong>Auto ICAO Lookup:</strong> {{ auto_icao_status }}</li>
                                <li><strong>Auto Delete Not Found:</strong> {{ auto_delete_status }}</li>
                            </ul>
                        </div>
                        
                        <h3>Update Settings:</h3>
                        {{ form|safe }}
                        """,
                        "form": form,
                        "alert_channel_name": alert_channel_name,
                        "alert_role_name": alert_role_name,
                        "auto_icao_status": "Enabled" if form.auto_icao.data else "Disabled",
                        "auto_delete_status": "Enabled" if form.auto_delete.data else "Disabled",
                    },
                }
            except ValueError:
                return {
                    "status": 1,
                    "notifications": [{"message": "Invalid channel or role ID. Please enter valid numeric IDs.", "category": "error"}]
                }
            except Exception as e:
                return {
                    "status": 1,
                    "notifications": [{"message": f"Error updating settings: {e}", "category": "error"}]
                }
        
        # Populate form with current values (only if not a successful submission)
        form.alert_channel.data = str(alert_channel_id or "")
        form.alert_role.data = str(alert_role_id or "")
        form.auto_icao.data = auto_icao
        form.auto_delete.data = auto_delete
        # Render the form using WTForms template
        return {
            "status": 0,
            "web_content": {
                "source": """
                <h2>SkySearch Guild Settings</h2>
                <p>Configure SkySearch settings for this guild.</p>
                
                <div style="margin-bottom: 20px;">
                    <h3>Current Settings:</h3>
                    <ul>
                        <li><strong>Alert Channel:</strong> {{ alert_channel_name }}</li>
                        <li><strong>Alert Role:</strong> {{ alert_role_name }}</li>
                        <li><strong>Auto ICAO Lookup:</strong> {{ auto_icao_status }}</li>
                        <li><strong>Auto Delete Not Found:</strong> {{ auto_delete_status }}</li>
                    </ul>
                </div>
                
                <h3>Update Settings:</h3>
                {{ form|safe }}
                """,
                "form": form,
                "alert_channel_name": alert_channel_name,
                "alert_role_name": alert_role_name,
                "auto_icao_status": "Enabled" if auto_icao else "Disabled",
                "auto_delete_status": "Enabled" if auto_delete else "Disabled",
            },
        } 
import typing
import discord
import wtforms
from redbot.core import commands
import datetime

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

    @dashboard_page(name="apistats", description="SkySearch API Statistics", methods=("GET",))
    async def dashboard_api_stats(self, **kwargs) -> typing.Dict[str, typing.Any]:
        """Show API request statistics in the dashboard."""
        cog = getattr(self, "_skysearch_cog", None)
        if not cog:
            return {"status": 0, "web_content": {"source": "<p>SkySearch cog not loaded.</p>"}}
        
        if not hasattr(cog.api, 'get_request_stats'):
            return {"status": 0, "web_content": {"source": "<p>API statistics not available.</p>"}}
        
        try:
            # Wait for stats to be initialized from config
            await cog.api.wait_for_stats_initialization()
            api_stats = cog.api.get_request_stats()
            
            # Format the statistics for display
            stats_html = f"""
            <div style="background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;">
                <h2 style="color: #ffffff;">📊 Airplanes.live API Statistics</h2>
                <p style="color: #cfcfcf;">Detailed request tracking and performance metrics for the airplanes.live API.</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                    <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41; color: #e6e6e6;">
                        <h3 style="color: #ffffff;">📈 Overall Statistics</h3>
                        <ul style="margin: 0; padding-left: 18px;">
                            <li><strong>Total Requests:</strong> {api_stats['total_requests']:,}</li>
                            <li><strong>Success Rate:</strong> {api_stats['success_rate']:.1f}%</li>
                            <li><strong>Last Request:</strong> {api_stats.get('last_request_time_formatted', 'Never')}</li>
                        </ul>
                    </div>
                
                    <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41; color: #e6e6e6;">
                        <h3 style="color: #ffffff;">✅ Success/Failure</h3>
                        <ul style="margin: 0; padding-left: 18px;">
                            <li><strong>Successful:</strong> {api_stats['successful_requests']:,}</li>
                            <li><strong>Failed:</strong> {api_stats['failed_requests']:,}</li>
                            <li><strong>Rate Limited:</strong> {api_stats['rate_limited_requests']:,}</li>
                        </ul>
                    </div>
                
                    <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41; color: #e6e6e6;">
                        <h3 style="color: #ffffff;">🌐 API Mode Usage</h3>
                        <ul style="margin: 0; padding-left: 18px;">
                            <li><strong>Primary API:</strong> {api_stats['api_mode_usage']['primary']:,}</li>
                            <li><strong>Fallback API:</strong> {api_stats['api_mode_usage']['fallback']:,}</li>
                        </ul>
                    </div>
                
                    <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41; color: #e6e6e6;">
                        <h3 style="color: #ffffff;">⚡ Performance</h3>
                        <ul style="margin: 0; padding-left: 18px;">
                            <li><strong>Avg Response Time:</strong> {api_stats['avg_response_time']:.3f}s</li>
                            <li><strong>Last 24h Requests:</strong> {api_stats['requests_last_24h']:,}</li>
                        </ul>
                    </div>
                </div>
            </div>
            """
            
            # Add top endpoints if available
            if api_stats['endpoint_usage']:
                top_endpoints = sorted(
                    api_stats['endpoint_usage'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
                
                endpoints_html = "<h3>🔗 Top Endpoints</h3><ul>"
                for endpoint, count in top_endpoints:
                    endpoints_html += f"<li><strong>{endpoint}:</strong> {count:,} requests</li>"
                endpoints_html += "</ul>"
                
                stats_html += f"""
                <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41; margin-top: 20px; color: #e6e6e6;">
                    {endpoints_html}
                </div>
                """
            
            # Add error details if any
            if api_stats['auth_failed_requests'] > 0 or api_stats['permission_denied_requests'] > 0:
                error_html = "<h3>⚠️ Error Details</h3><ul>"
                if api_stats['auth_failed_requests'] > 0:
                    error_html += f"<li><strong>Authentication Failed:</strong> {api_stats['auth_failed_requests']:,}</li>"
                if api_stats['permission_denied_requests'] > 0:
                    error_html += f"<li><strong>Permission Denied:</strong> {api_stats['permission_denied_requests']:,}</li>"
                error_html += "</ul>"
                
                stats_html += f"""
                <div style="background-color: #3a2f00; padding: 20px; border-radius: 8px; border: 1px solid #806b00; margin-top: 20px; color: #ffe58f;">
                    {error_html}
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
                    "source": f"<p>Error loading API statistics: {str(e)}</p>"
                },
                "notifications": [{"message": f"Error loading API statistics: {str(e)}", "category": "error"}]
            }

    @dashboard_page(name="lookup", description="SkySearch Aircraft Lookup", methods=("GET", "POST"), context_ids=["guild_id"])
    async def dashboard_aircraft_lookup(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
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
            ], render_kw={"class": "form-select"})
            search_value = wtforms.StringField("Search Value", render_kw={"class": "form-field", "placeholder": "Enter search value..."})
            submit = wtforms.SubmitField("Search Aircraft", render_kw={"class": "form-submit"})
        
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
                            <div style=\"background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;\">
                                <h2 style=\"color: #ffffff;\">SkySearch Aircraft Lookup</h2>
                                <p style=\"color: #cfcfcf;\">Search for aircraft by ICAO code, callsign, registration, or aircraft type.</p>
                                
                                <div style=\"margin-bottom: 20px;\">
                                    <h3 style=\"color: #ffffff;\">Search Aircraft:</h3>
                                    <div style=\"background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41;\">
                                        <style>
                                            .form-container {
                                                display: flex;
                                                flex-direction: column;
                                                gap: 15px;
                                            }
                                            .form-row {
                                                display: flex;
                                                align-items: center;
                                                gap: 10px;
                                                flex-wrap: wrap;
                                            }
                                            .form-label {
                                                color: #ffffff;
                                                font-weight: bold;
                                                min-width: 100px;
                                            }
                                            .form-field {
                                                background-color: #1e1f22;
                                                border: 1px solid #3a3d41;
                                                border-radius: 4px;
                                                color: #e6e6e6;
                                                padding: 8px 12px;
                                                font-size: 14px;
                                            }
                                            .form-field:focus {
                                                outline: none;
                                                border-color: #5865f2;
                                                box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
                                            }
                                            .form-select {
                                                background-color: #1e1f22;
                                                border: 1px solid #3a3d41;
                                                border-radius: 4px;
                                                color: #e6e6e6;
                                                padding: 8px 12px;
                                                font-size: 14px;
                                                min-width: 150px;
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
                                            .form-submit:active {
                                                background-color: #3c45a5;
                                            }
                                        </style>
                                        <div class=\"form-container\">
                                            {{ form|safe }}
                                        </div>
                                    </div>
                                </div>
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
                            <div style=\"background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;\">
                                <h2 style=\"color: #ffffff;\">SkySearch Aircraft Lookup</h2>
                                <p style=\"color: #cfcfcf;\">Search for aircraft by ICAO code, callsign, registration, or aircraft type.</p>
                                
                                <div style=\"margin-bottom: 20px;\">
                                    <h3 style=\"color: #ffffff;\">Search Aircraft:</h3>
                                    <div style=\"background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41;\">
                                        <style>
                                            .form-container {
                                                display: flex;
                                                flex-direction: column;
                                                gap: 15px;
                                            }
                                            .form-row {
                                                display: flex;
                                                align-items: center;
                                                gap: 10px;
                                                flex-wrap: wrap;
                                            }
                                            .form-label {
                                                color: #ffffff;
                                                font-weight: bold;
                                                min-width: 100px;
                                            }
                                            .form-field {
                                                background-color: #1e1f22;
                                                border: 1px solid #3a3d41;
                                                border-radius: 4px;
                                                color: #e6e6e6;
                                                padding: 8px 12px;
                                                font-size: 14px;
                                            }
                                            .form-field:focus {
                                                outline: none;
                                                border-color: #5865f2;
                                                box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
                                            }
                                            .form-select {
                                                background-color: #1e1f22;
                                                border: 1px solid #3a3d41;
                                                border-radius: 4px;
                                                color: #e6e6e6;
                                                padding: 8px 12px;
                                                font-size: 14px;
                                                min-width: 150px;
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
                                            .form-submit:active {
                                                background-color: #3c45a5;
                                            }
                                        </style>
                                        <div class=\"form-container\">
                                            {{ form|safe }}
                                        </div>
                                    </div>
                                </div>
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
                            # Get photo for the aircraft using full aircraft data
                            image_url, photographer = await cog.helpers.get_photo_by_aircraft_data(aircraft_data)
                            
                            # Extract ICAO for later use
                            icao = aircraft_data.get('hex', '')
                            if icao:
                                icao = icao.upper()
                            
                            # Create comprehensive aircraft info HTML
                            description = f"{aircraft_data.get('desc', 'N/A')}"
                            if aircraft_data.get('year', None) is not None:
                                description += f" ({aircraft_data.get('year')})"
                            
                            callsign = aircraft_data.get('flight', 'N/A').strip()
                            if not callsign or callsign == 'N/A':
                                callsign = 'BLOCKED'
                            
                            registration = aircraft_data.get('reg', 'N/A')
                            if registration and registration != 'N/A':
                                registration = registration.upper()
                            
                            # Altitude information
                            altitude = aircraft_data.get('alt_baro', 'N/A')
                            if altitude == 'ground':
                                altitude_text = "On ground"
                            elif altitude != 'N/A':
                                if isinstance(altitude, int):
                                    altitude = "{:,}".format(altitude)
                                altitude_text = f"{altitude} ft"
                            else:
                                altitude_text = "N/A"
                            
                            # Position information
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
                            
                            # Squawk code with emergency detection
                            squawk_code = aircraft_data.get('squawk', 'N/A')
                            emergency_squawk_codes = ['7500', '7600', '7700']
                            if squawk_code in emergency_squawk_codes:
                                squawk_style = 'color: red; font-weight: bold;'
                                if squawk_code == '7500':
                                    emergency_status = "🚨 Aircraft reports it's been hijacked"
                                elif squawk_code == '7600':
                                    emergency_status = "🚨 Aircraft has lost radio contact"
                                elif squawk_code == '7700':
                                    emergency_status = "🚨 Aircraft has declared a general emergency"
                            else:
                                squawk_style = ''
                                emergency_status = "Aircraft reports normal conditions"
                            
                            # Aircraft model
                            aircraft_model = aircraft_data.get('t', 'N/A')
                            
                            # Speed information
                            ground_speed_knots = aircraft_data.get('gs', 'N/A')
                            if ground_speed_knots != 'N/A':
                                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
                                speed_text = f"{ground_speed_mph} mph"
                            else:
                                speed_text = "N/A"
                            
                            # Heading information
                            heading = aircraft_data.get('true_heading', None)
                            if heading is not None:
                                heading_text = f"{heading}°"
                            else:
                                heading_text = "N/A"
                            
                            # Category information
                            category_code_to_label = {
                                "A0": "No info available", "A1": "Light aircraft", "A2": "Small aircraft",
                                "A3": "Large aircraft", "A4": "High vortex large aircraft", "A5": "Heavy aircraft",
                                "A6": "High performance aircraft", "A7": "Rotorcraft", "B0": "No info available",
                                "B1": "Glider / sailplane", "B2": "Lighter-than-air", "B3": "Parachutist / skydiver",
                                "B4": "Ultralight / hang-glider / paraglider", "B5": "Reserved", "B6": "UAV",
                                "B7": "Space / trans-atmospheric vehicle", "C0": "No info available",
                                "C1": "Emergency vehicle", "C2": "Service vehicle", "C3": "Point obstacle",
                                "C4": "Cluster obstacle", "C5": "Line obstacle", "C6": "Reserved", "C7": "Reserved"
                            }
                            category = aircraft_data.get('category', None)
                            if category is not None:
                                category_text = category_code_to_label.get(category, "Unknown category")
                            else:
                                category_text = "N/A"
                            
                            # Operator information
                            operator = aircraft_data.get('ownOp', 'N/A')
                            
                            # Timing information
                            last_seen = aircraft_data.get('seen', 'N/A')
                            if last_seen != 'N/A':
                                last_seen_text = "Just now" if float(last_seen) < 1 else f"{int(float(last_seen))} seconds ago"
                            else:
                                last_seen_text = "N/A"
                            
                            last_seen_pos = aircraft_data.get('seen_pos', 'N/A')
                            if last_seen_pos != 'N/A':
                                last_seen_pos_text = "Just now" if float(last_seen_pos) < 1 else f"{int(float(last_seen_pos))} seconds ago"
                            else:
                                last_seen_pos_text = "N/A"
                            
                            # Altitude trend information
                            baro_rate = aircraft_data.get('baro_rate', 'N/A')
                            if baro_rate == 'N/A':
                                altitude_trend_text = "Altitude trends unavailable, not enough data"
                            else:
                                baro_rate_fps = round(int(baro_rate) / 60, 2)  # Convert feet per minute to feet per second
                                if abs(baro_rate_fps) < 50/60:
                                    altitude_trend_text = "Maintaining consistent altitude"
                                elif baro_rate_fps > 0:
                                    altitude_trend_text = f"Climbing {baro_rate_fps} feet/sec"
                                else:
                                    altitude_trend_text = f"Descending {abs(baro_rate_fps)} feet/sec"
                            
                            # Asset intelligence information
                            asset_intelligence = []
                            if icao and icao.upper() in cog.law_enforcement_icao_set:
                                asset_intelligence.append("👮 Known for use by state law enforcement")
                            if icao and icao.upper() in cog.military_icao_set:
                                asset_intelligence.append("🪖 Known for use in military and government")
                            if icao and icao.upper() in cog.medical_icao_set:
                                asset_intelligence.append("🏥 Known for use in medical response and transport")
                            if icao and icao.upper() in cog.suspicious_icao_set:
                                asset_intelligence.append("⚠️ Exhibits suspicious flight or surveillance activity")
                            if icao and icao.upper() in cog.global_prior_known_accident_set:
                                asset_intelligence.append("💥 Prior involved in one or more documented accidents")
                            if icao and icao.upper() in cog.ukr_conflict_set:
                                asset_intelligence.append("🇺🇦 Utilized within the Russo-Ukrainian conflict")
                            if icao and icao.upper() in cog.newsagency_icao_set:
                                asset_intelligence.append("📰 Used by news or media organization")
                            if icao and icao.upper() in cog.balloons_icao_set:
                                asset_intelligence.append("🎈 Aircraft is a balloon")
                            if icao and icao.upper() in cog.agri_utility_set:
                                asset_intelligence.append("🌽 Used for agriculture surveys, easement validation, or land inspection")
                            
                            # Build asset intelligence HTML
                            asset_intelligence_html = ""
                            if asset_intelligence:
                                asset_intelligence_html = f'''
                                <div style="margin-top: 20px;">
                                    <h4 style="color: #000000; margin-bottom: 10px;">Asset Intelligence</h4>
                                    {chr(10).join([f'<p style="margin: 5px 0;">{intel}</p>' for intel in asset_intelligence])}
                                </div>
                                '''
                            
                            globe_link = f"https://globe.airplanes.live/?icao={icao}"
                            
                            result_html += f'''
                            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; background-color: #808080; color: #000000;">
                                <h3 style="margin-top: 0; color: #000000; border-bottom: 2px solid #666; padding-bottom: 10px;">{description}</h3>
                                
                                <div style="display: flex; gap: 30px;">
                                    <div style="flex: 1;">
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                            <div>
                                                <h4 style="color: #000000; margin-bottom: 10px;">Flight Information</h4>
                                                <p><strong>Callsign:</strong> {callsign}</p>
                                                <p><strong>Registration:</strong> {registration}</p>
                                                <p><strong>ICAO:</strong> {icao}</p>
                                                <p><strong>Model:</strong> {aircraft_model}</p>
                                                <p><strong>Category:</strong> {category_text}</p>
                                                <p><strong>Operated by:</strong> {operator}</p>
                                            </div>
                                            
                                            <div>
                                                <h4 style="color: #000000; margin-bottom: 10px;">Position & Navigation</h4>
                                                <p><strong>Altitude:</strong> {altitude_text}</p>
                                                <p><strong>Speed:</strong> {speed_text}</p>
                                                <p><strong>Heading:</strong> {heading_text}</p>
                                                <p><strong>Position:</strong> {position_text}</p>
                                                <p><strong>Squawk:</strong> <span style="{squawk_style}">{squawk_code}</span></p>
                                                <p><strong>Altitude Trend:</strong> {altitude_trend_text}</p>
                                            </div>
                                        </div>
                                        
                                        <div style="margin-top: 20px;">
                                            <h4 style="color: #000000; margin-bottom: 10px;">Timing Information</h4>
                                            <p><strong>Last signal:</strong> {last_seen_text}</p>
                                            <p><strong>Last position:</strong> {last_seen_pos_text}</p>
                                            <p><strong>Flight status:</strong> {emergency_status}</p>
                                        </div>
                                        
                                        {asset_intelligence_html}
                                    </div>
                                    
                                    <div style="flex: 0 0 250px;">
                                        <h4 style="color: #000000; margin-bottom: 10px;">Aircraft Photo</h4>
                                        {f'<img src="{image_url}" alt="Aircraft photo" style="max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #666;">' if image_url else '<div style="background-color: #666; padding: 40px; text-align: center; border-radius: 8px;"><p style="color: #999; font-style: italic;">No photo available</p></div>'}
                                        {f'<p style="font-size: 12px; color: #666; margin-top: 8px; text-align: center;">Photo by: {photographer}</p>' if photographer else ''}
                                    </div>
                                </div>
                                
                                <div style="margin-top: 20px; text-align: center;">
                                    <a href="{globe_link}" target="_blank" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">View on Globe</a>
                                </div>
                            </div>
                            '''
                        
                        if len(aircraft_list) > 5:
                            result_html += f'<p style="color: #666; font-style: italic;">Showing first 5 of {len(aircraft_list)} results</p>'
                        
                        result_html += '</div>'
                    else:
                        result_html = '''
                        <div style="margin-top: 20px;">
                            <h3 style="color: #ffffff;">No Results Found</h3>
                            <p style="color: #cfcfcf;">No aircraft found matching your search criteria. Please try a different search term.</p>
                        </div>
                        '''
                else:
                    result_html = '''
                    <div style="margin-top: 20px;">
                        <h3 style="color: #ffffff;">Error</h3>
                        <p style="color: #cfcfcf;">Unable to retrieve aircraft information. Please check your search terms and try again.</p>
                    </div>
                    '''
                    
            except Exception as e:
                result_html = f'''
                <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
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
                "source": """
                <div style=\"background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;\">
                    <h2 style=\"color: #ffffff;\">SkySearch Aircraft Lookup</h2>
                    <p style=\"color: #cfcfcf;\">Search for aircraft by ICAO code, callsign, registration, or aircraft type.</p>
                    
                    <div style=\"margin-bottom: 20px;\">
                        <h3 style=\"color: #ffffff;\">Search Aircraft:</h3>
                        <div style=\"background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41;\">
                            <style>
                                .form-container {
                                    display: flex;
                                    flex-direction: column;
                                    gap: 15px;
                                }
                                .form-row {
                                    display: flex;
                                    align-items: center;
                                    gap: 10px;
                                    flex-wrap: wrap;
                                }
                                .form-label {
                                    color: #ffffff;
                                    font-weight: bold;
                                    min-width: 100px;
                                }
                                .form-field {
                                    background-color: #1e1f22;
                                    border: 1px solid #3a3d41;
                                    border-radius: 4px;
                                    color: #e6e6e6;
                                    padding: 8px 12px;
                                    font-size: 14px;
                                }
                                .form-field:focus {
                                    outline: none;
                                    border-color: #5865f2;
                                    box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
                                }
                                .form-select {
                                    background-color: #1e1f22;
                                    border: 1px solid #3a3d41;
                                    border-radius: 4px;
                                    color: #e6e6e6;
                                    padding: 8px 12px;
                                    font-size: 14px;
                                    min-width: 150px;
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
                                .form-submit:active {
                                    background-color: #3c45a5;
                                }
                            </style>
                            <div class=\"form-container\">
                                {{ form|safe }}
                            </div>
                        </div>
                    </div>
                    
                    {{ result_html|safe }}
                </div>
                """,
                "form": form,
                "result_html": result_html,
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
            custom_alerts = await config.custom_alerts()
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
        
        # WTForms form definition for settings
        class SettingsForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="settings_")
            alert_channel = wtforms.StringField("Alert Channel ID")
            alert_role = wtforms.StringField("Alert Role ID")
            auto_icao = wtforms.BooleanField("Auto ICAO Lookup")
            auto_delete = wtforms.BooleanField("Auto Delete Not Found")
            submit = wtforms.SubmitField("Save Settings")
        
        # WTForms form definition for adding alerts
        class AlertForm(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="alert_")
            alert_type = wtforms.SelectField("Alert Type", choices=[
                ("icao", "ICAO Hex Code"),
                ("callsign", "Flight Callsign"),
                ("squawk", "Squawk Code"),
                ("type", "Aircraft Type"),
                ("reg", "Registration")
            ], render_kw={"class": "form-select"})
            alert_value = wtforms.StringField("Alert Value", render_kw={"class": "form-field", "placeholder": "Enter value to monitor..."})
            cooldown = wtforms.IntegerField("Cooldown (minutes)", render_kw={"class": "form-field", "placeholder": "5", "min": "1", "max": "1440"})
            custom_channel = wtforms.StringField("Custom Channel ID (optional)", render_kw={"class": "form-field", "placeholder": "Leave empty to use default alert channel"})
            submit_alert = wtforms.SubmitField("Add Alert", render_kw={"class": "form-submit"})
        
        settings_form = SettingsForm()
        alert_form = AlertForm()
        result_html = ""
        
        # Handle settings form submission
        if settings_form.validate_on_submit():
            try:
                # Validate and update config
                alert_channel_val = int(settings_form.alert_channel.data) if settings_form.alert_channel.data else None
                alert_role_val = int(settings_form.alert_role.data) if settings_form.alert_role.data else None
                
                await config.alert_channel.set(alert_channel_val)
                await config.alert_role.set(alert_role_val)
                await config.auto_icao.set(settings_form.auto_icao.data)
                await config.auto_delete_not_found.set(settings_form.auto_delete.data)
                
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
                
                result_html = '''
                <div style="margin-top: 20px; padding: 10px; background-color: #152b15; border: 1px solid #245a24; border-radius: 4px; color: #b8ffb8;">
                    <strong>Success:</strong> Settings updated successfully!
                </div>
                '''
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
        
        # Handle alert form submission
        if alert_form.validate_on_submit():
            try:
                alert_type = alert_form.alert_type.data
                alert_value = alert_form.alert_value.data.strip()
                cooldown = alert_form.cooldown.data or 5
                custom_channel_id = alert_form.custom_channel.data.strip() if alert_form.custom_channel.data else None
                
                if not alert_value:
                    result_html = '''
                    <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                        <strong>Error:</strong> Please enter a value for the alert.
                    </div>
                    '''
                elif cooldown < 1 or cooldown > 1440:
                    result_html = '''
                    <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                        <strong>Error:</strong> Cooldown must be between 1 and 1440 minutes.
                    </div>
                    '''
                elif custom_channel_id and not custom_channel_id.isdigit():
                    result_html = '''
                    <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                        <strong>Error:</strong> Custom channel ID must be a valid numeric ID.
                    </div>
                    '''
                elif custom_channel_id and not guild.get_channel(int(custom_channel_id)):
                    result_html = '''
                    <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                        <strong>Error:</strong> Custom channel not found. Please enter a valid channel ID.
                    </div>
                    '''
                else:
                    alert_id = f"{alert_type}_{alert_value.lower()}"
                    
                    if alert_id in custom_alerts:
                        result_html = '''
                        <div style="margin-top: 20px; padding: 10px; background-color: #2b2e18; border: 1px solid #5a5a24; border-radius: 4px; color: #ffffb8;">
                            <strong>Warning:</strong> An alert for this value already exists.
                        </div>
                        '''
                    else:
                        custom_alerts[alert_id] = {
                            'type': alert_type,
                            'value': alert_value,
                            'cooldown': cooldown,
                            'custom_channel': int(custom_channel_id) if custom_channel_id else None,
                            'created_by': 'dashboard_user',
                            'created_at': datetime.datetime.utcnow().isoformat(),
                            'last_triggered': None
                        }
                        
                        await config.custom_alerts.set(custom_alerts)
                        channel_info = ""
                        if custom_channel_id:
                            channel = guild.get_channel(int(custom_channel_id))
                            channel_name = channel.name if channel else f"Channel {custom_channel_id}"
                            channel_info = f" to #{channel_name}"
                        else:
                            channel_info = " to default alert channel"
                        
                        result_html = f'''
                        <div style="margin-top: 20px; padding: 10px; background-color: #152b15; border: 1px solid #245a24; border-radius: 4px; color: #b8ffb8;">
                            <strong>Success:</strong> Added alert for {alert_type} '{alert_value}' with {cooldown} minute cooldown{channel_info}.
                        </div>
                        '''
                        
            except Exception as e:
                result_html = f'''
                <div style="margin-top: 20px; padding: 10px; background-color: #2b1518; border: 1px solid #5a1e24; border-radius: 4px; color: #ffb3b8;">
                    <strong>Error:</strong> An error occurred while adding the alert: {str(e)}
                </div>
                '''
        
        # Handle remove alert action
        if kwargs.get("request") and kwargs["request"].method == "POST":
            form_data = kwargs["request"].form
            if form_data.get("action") == "remove_alert":
                alert_id = form_data.get("alert_id")
                if alert_id and alert_id in custom_alerts:
                    del custom_alerts[alert_id]
                    await config.custom_alerts.set(custom_alerts)
                    result_html = f'''
                    <div style="margin-top: 20px; padding: 10px; background-color: #152b15; border: 1px solid #245a24; border-radius: 4px; color: #b8ffb8;">
                        <strong>Success:</strong> Removed alert {alert_id}.
                    </div>
                    '''
        
        # Build alerts list HTML
        alerts_html = ""
        if custom_alerts:
            alerts_html = '<div style="margin-top: 20px;"><h3>Current Custom Alerts:</h3><div style="background-color: #2b2e34; padding: 15px; border-radius: 8px; border: 1px solid #3a3d41;">'
            for alert_id, alert_data in custom_alerts.items():
                created_at = datetime.datetime.fromisoformat(alert_data['created_at'])
                last_triggered = "Never"
                if alert_data['last_triggered']:
                    last_triggered = datetime.datetime.fromisoformat(alert_data['last_triggered']).strftime("%Y-%m-%d %H:%M UTC")
                
                # Get channel information
                custom_channel_id = alert_data.get('custom_channel')
                channel_info = ""
                if custom_channel_id:
                    channel = guild.get_channel(custom_channel_id)
                    channel_name = channel.name if channel else f"Channel {custom_channel_id}"
                    channel_info = f" | Channel: #{channel_name}"
                else:
                    channel_info = " | Channel: Default"
                
                alerts_html += f'''
                <div style="margin-bottom: 15px; padding: 10px; background-color: #1e1f22; border-radius: 4px; border-left: 4px solid #5865f2;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>🔔 {alert_id}</strong><br>
                            <span style="color: #cfcfcf;">Type: {alert_data['type']} | Value: {alert_data['value']} | Cooldown: {alert_data['cooldown']} min{channel_info}</span><br>
                            <span style="color: #8a8a8a; font-size: 12px;">Created: {created_at.strftime('%Y-%m-%d %H:%M UTC')} | Last Triggered: {last_triggered}</span>
                        </div>
                        <form method="POST" action="/dashboard/guild" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="action" value="remove_alert">
                            <input type="hidden" name="alert_id" value="{alert_id}">
                            <button type="submit" style="background-color: #ff4545; border: none; border-radius: 4px; color: white; padding: 5px 10px; cursor: pointer; font-size: 12px;">Remove</button>
                        </form>
                    </div>
                </div>
                '''
            alerts_html += '</div></div>'
        else:
            alerts_html = '''
            <div style="margin-top: 20px; padding: 20px; background-color: #2b2e34; border-radius: 8px; border: 1px solid #3a3d41; text-align: center; color: #8a8a8a;">
                <h3>No Custom Alerts</h3>
                <p>No custom alerts are currently configured for this server.</p>
            </div>
            '''
        
        # Populate form with current values (only if not a successful submission)
        settings_form.alert_channel.data = str(alert_channel_id or "")
        settings_form.alert_role.data = str(alert_role_id or "")
        settings_form.auto_icao.data = auto_icao
        settings_form.auto_delete.data = auto_delete
        # Render the form using WTForms template
        return {
            "status": 0,
            "web_content": {
                "source": """
                <div style="background-color: #1e1f22; padding: 20px; border-radius: 8px; color: #e6e6e6;">
                    <h2 style="color: #ffffff;">SkySearch Guild Settings</h2>
                    <p style="color: #cfcfcf;">Configure SkySearch settings and custom alerts for this guild.</p>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #ffffff;">Current Settings:</h3>
                        <div style="background-color: #2b2e34; padding: 15px; border-radius: 8px; border: 1px solid #3a3d41;">
                            <ul style="margin: 0; padding-left: 20px;">
                                <li><strong>Alert Channel:</strong> {{ alert_channel_name }}</li>
                                <li><strong>Alert Role:</strong> {{ alert_role_name }}</li>
                                <li><strong>Auto ICAO Lookup:</strong> {{ auto_icao_status }}</li>
                                <li><strong>Auto Delete Not Found:</strong> {{ auto_delete_status }}</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #ffffff;">Update Settings:</h3>
                        <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41;">
                            <style>
                                .form-container {
                                    display: flex;
                                    flex-direction: column;
                                    gap: 15px;
                                }
                                .form-row {
                                    display: flex;
                                    align-items: center;
                                    gap: 10px;
                                    flex-wrap: wrap;
                                }
                                .form-label {
                                    color: #ffffff;
                                    font-weight: bold;
                                    min-width: 100px;
                                }
                                .form-field {
                                    background-color: #1e1f22;
                                    border: 1px solid #3a3d41;
                                    border-radius: 4px;
                                    color: #e6e6e6;
                                    padding: 8px 12px;
                                    font-size: 14px;
                                }
                                .form-field:focus {
                                    outline: none;
                                    border-color: #5865f2;
                                    box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
                                }
                                .form-select {
                                    background-color: #1e1f22;
                                    border: 1px solid #3a3d41;
                                    border-radius: 4px;
                                    color: #e6e6e6;
                                    padding: 8px 12px;
                                    font-size: 14px;
                                    min-width: 150px;
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
                                .form-submit:active {
                                    background-color: #3c45a5;
                                }
                            </style>
                            <div class="form-container">
                                {{ settings_form|safe }}
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #ffffff;">Add Custom Alert:</h3>
                        <div style="background-color: #2b2e34; padding: 20px; border-radius: 8px; border: 1px solid #3a3d41;">
                            <div class="form-container">
                                {{ alert_form|safe }}
                            </div>
                        </div>
                    </div>
                    
                    {{ alerts_html|safe }}
                    {{ result_html|safe }}
                </div>
                """,
                "settings_form": settings_form,
                "alert_form": alert_form,
                "alerts_html": alerts_html,
                "result_html": result_html,
                "alert_channel_name": alert_channel_name,
                "alert_role_name": alert_role_name,
                "auto_icao_status": "Enabled" if auto_icao else "Disabled",
                "auto_delete_status": "Enabled" if auto_delete else "Disabled",
            },
        }

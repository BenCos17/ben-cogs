"""
Airport commands for SkySearch cog
"""

import discord
import aiohttp
import asyncio
import re
from datetime import datetime
from typing import Optional
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from ..utils.api import APIManager
from ..utils.helpers import HelperUtils
from ..utils.xml_parser import XMLParser
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n

# Internationalization
_ = Translator("Skysearch", __file__)


class FAAStatusRefreshButton(discord.ui.Button):
    """Button to refresh FAA status data."""
    
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Refresh", emoji="🔄", custom_id="faa_status_refresh")
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, FAAStatusView) or view.airport_commands is None:
            await interaction.response.defer()
            return
        await interaction.response.defer()
        result = await view.airport_commands._faa_fetch_data(view.airport_code)
        if result is None:
            await interaction.followup.send("Could not refresh; FAA API may be unavailable.", ephemeral=True)
            return
        ground_delays, arrival_departure_delays, closures, update_time = result
        view.ground_delays = ground_delays
        view.arrival_departure_delays = arrival_departure_delays
        view.closures = closures
        view.update_time = update_time
        embed = view.build_embed(view.current_filter)
        await interaction.edit_original_response(embed=embed, view=view)


class FAAStatusView(discord.ui.View):
    """View with dropdown to filter FAA status by delay type and optional Refresh button."""
    
    def __init__(self, ground_delays, arrival_departure_delays, closures, update_time, airport_code=None, airport_commands=None):
        super().__init__(timeout=600)  # 10 minute timeout
        self.ground_delays = ground_delays
        self.arrival_departure_delays = arrival_departure_delays
        self.closures = closures
        self.update_time = update_time
        self.airport_code = airport_code
        self.airport_commands = airport_commands
        self.current_filter = "all"
        
        # Build dropdown options
        options = [
            discord.SelectOption(
                label="All Issues",
                value="all",
                description="Show all delays and closures",
                emoji="✈️",
                default=True
            )
        ]
        
        if ground_delays:
            options.append(discord.SelectOption(
                label="Ground Delays",
                value="ground",
                description=f"{len(ground_delays)} ground delay program(s)",
                emoji="🛫"
            ))
        
        if arrival_departure_delays:
            options.append(discord.SelectOption(
                label="Arrival/Departure Delays",
                value="arrdep",
                description=f"{len(arrival_departure_delays)} delay(s)",
                emoji="🛬"
            ))
        
        if closures:
            options.append(discord.SelectOption(
                label="Closures",
                value="closures",
                description=f"{len(closures)} closure(s)",
                emoji="🚫"
            ))
        
        if len(options) > 1:
            self.select_menu = discord.ui.Select(
                placeholder="Filter by delay type...",
                options=options,
                min_values=1,
                max_values=1
            )
            self.select_menu.callback = self.on_select
            self.add_item(self.select_menu)
        
        # Refresh button (when airport_commands is provided so we can re-fetch)
        if airport_commands is not None:
            self.add_item(FAAStatusRefreshButton())
    
    async def on_select(self, interaction: discord.Interaction):
        """Handle dropdown selection."""
        values = interaction.data.get('values') if isinstance(interaction.data, dict) else None
        if not values:
            await interaction.response.defer()
            return
        selected = values[0]
        self.current_filter = selected
        
        # Update default option
        for option in self.select_menu.options:
            option.default = (option.value == selected)
        
        # Build new embed
        embed = self.build_embed(selected)
        await interaction.response.edit_message(embed=embed, view=self)
    
    def build_embed(self, filter_type="all"):
        """Build embed based on filter type."""
        embed = discord.Embed(
            title="✈️ FAA National Airspace Status",
            color=0x2b2d31
        )
        
        # Add filter indicator to footer
        filter_text = {
            "all": "All Issues",
            "ground": "Ground Delays Only",
            "arrdep": "Arrival/Departure Delays Only",
            "closures": "Closures Only"
        }.get(filter_type, "All Issues")
        
        embed.set_footer(text=f"{filter_text} • Updated: {self.update_time} • Times in UTC • Data refreshes every 60s")
        
        field_count = 0
        max_fields = 25
        
        # Add Ground Delay Programs
        if filter_type in ("all", "ground") and self.ground_delays:
            for delay in self.ground_delays[:8]:
                if field_count >= max_fields:
                    break
                delay_info = f"`{delay['avg']}` avg • `{delay['max']}` max"
                value = f"{delay_info}\n**Reason:** {delay['reason']}"
                embed.add_field(
                    name=f"🛫 `{delay['arpt']}` Ground Delay",
                    value=value,
                    inline=False
                )
                field_count += 1
        
        # Add Arrival/Departure Delays
        if filter_type in ("all", "arrdep") and self.arrival_departure_delays:
            for delay in self.arrival_departure_delays[:8]:
                if field_count >= max_fields:
                    break
                emoji = "🛬" if delay['type'].lower() == "arrival" else "🛫"
                type_name = delay['type']
                
                delay_parts = []
                if delay['min'] and delay['max']:
                    delay_parts.append(f"`{delay['min']}` - `{delay['max']}`")
                elif delay['min']:
                    delay_parts.append(f"`{delay['min']}` min")
                elif delay['max']:
                    delay_parts.append(f"`{delay['max']}` max")
                
                value = ""
                if delay_parts:
                    value = f"{' • '.join(delay_parts)}\n"
                
                value += f"**Reason:** {delay['reason']}"
                
                if delay['trend']:
                    trend_emoji = "📈" if delay['trend'].lower() == "increasing" else "📉" if delay['trend'].lower() == "decreasing" else "➡️"
                    value += f" {trend_emoji}"
                
                embed.add_field(
                    name=f"{emoji} `{delay['arpt']}` {type_name} Delay",
                    value=value,
                    inline=False
                )
                field_count += 1
        
        # Add Airport Closures
        if filter_type in ("all", "closures") and self.closures:
            for closure in self.closures[:8]:
                if field_count >= max_fields:
                    break
                reason = closure['reason']
                phone_match = re.search(r'(\d{3}-\d{3}-\d{4})', reason)
                phone = phone_match.group(1) if phone_match else None
                
                if phone:
                    reason = reason.replace(phone, "").strip()
                    reason = re.sub(r'\s+', ' ', reason)
                
                value = f"**{reason}**"
                if phone:
                    value += f"\n📞 Contact: `{phone}`"
                
                timing_parts = []
                if closure['start']:
                    timing_parts.append(f"Started: `{closure['start']}`")
                if closure['reopen']:
                    timing_parts.append(f"Reopens: `{closure['reopen']}`")
                
                if timing_parts:
                    value += f"\n\n{' • '.join(timing_parts)}"
                
                embed.add_field(
                    name=f"🚫 `{closure['arpt']}` Closure",
                    value=value,
                    inline=False
                )
                field_count += 1
        
        # Add note if no results for filter
        if field_count == 0:
            embed.description = f"✅ No {filter_text.lower()} found."
        
        # Add note if we hit the limit
        if field_count >= max_fields:
            embed.add_field(
                name="⚠️ Display Limit",
                value="Showing first 25 items. Use `*airport faastatus <code>` to filter by airport.",
                inline=False
            )
        
        return embed


class AVWXRefreshButton(discord.ui.Button):
    """Button to refresh AVWX data."""

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Refresh", emoji="🔄", custom_id="avwx_refresh")

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, AVWXWeatherView) or view.airport_commands is None:
            await interaction.response.defer()
            return
        await interaction.response.defer()
        reports, error = await view.airport_commands._avwx_fetch_bundle(view.station_code)
        if error:
            await interaction.followup.send(error, ephemeral=True)
            return
        view.report_data = reports
        embed = view.build_embed(view.current_filter)
        await interaction.edit_original_response(embed=embed, view=view)


class AVWXWeatherView(discord.ui.View):
    """View for switching between AVWX overview, METAR, and TAF."""

    def __init__(self, station_code, report_data, airport_commands=None, initial_filter="overview"):
        super().__init__(timeout=600)
        self.station_code = station_code.upper()
        self.report_data = report_data
        self.airport_commands = airport_commands
        self.current_filter = initial_filter

        options = [
            discord.SelectOption(label="Overview", value="overview", description="Show combined aviation weather overview", emoji="🧭", default=initial_filter == "overview"),
            discord.SelectOption(label="METAR", value="metar", description="Show current observation details", emoji="🌤️", default=initial_filter == "metar"),
            discord.SelectOption(label="TAF", value="taf", description="Show current terminal forecast", emoji="📈", default=initial_filter == "taf"),
        ]

        self.select_menu = discord.ui.Select(
            placeholder="Select AVWX report view...",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.select_menu.callback = self.on_select
        self.add_item(self.select_menu)
        self.add_item(AVWXRefreshButton())

    async def on_select(self, interaction: discord.Interaction):
        values = interaction.data.get("values") if isinstance(interaction.data, dict) else None
        if not values:
            await interaction.response.defer()
            return
        selected = values[0]
        self.current_filter = selected
        for option in self.select_menu.options:
            option.default = option.value == selected
        embed = self.build_embed(selected)
        await interaction.response.edit_message(embed=embed, view=self)

    def build_embed(self, filter_type="overview"):
        report_data = self.report_data or {}
        metar = report_data.get("metar") or {}
        taf = report_data.get("taf") or {}
        summary = report_data.get("summary") or {}
        info = (metar.get("info") or taf.get("info") or summary.get("info") or {})

        station_name = info.get("name") or self.station_code
        title_prefix = {
            "overview": "AVWX Overview",
            "metar": "AVWX METAR",
            "taf": "AVWX TAF",
        }.get(filter_type, "AVWX Weather")
        embed = discord.Embed(title=f"{title_prefix} - {self.station_code}", color=0xfffffe)

        location_bits = [info.get("city"), info.get("country")]
        location = ", ".join(part for part in location_bits if part)
        description_parts = []
        if station_name and station_name != self.station_code:
            description_parts.append(f"**{station_name}**")
        if location:
            description_parts.append(location)
        if description_parts:
            embed.description = "\n".join(description_parts)

        meta = metar.get("meta") or taf.get("meta") or summary.get("meta") or {}
        timestamp = meta.get("timestamp")
        if timestamp:
            embed.set_footer(text=f"AVWX data refreshed: {timestamp}")

        if filter_type == "overview":
            self._add_overview_fields(embed, summary, metar, taf)
        elif filter_type == "metar":
            self._add_metar_fields(embed, metar)
        else:
            self._add_taf_fields(embed, taf)

        return embed

    def _add_overview_fields(self, embed: discord.Embed, summary: dict, metar: dict, taf: dict):
        summary_metar = summary.get("metar") or {}
        summary_taf = summary.get("taf") or {}

        rules = summary_metar.get("flight_rules") or metar.get("flight_rules") or "Unknown"
        visibility = (summary_metar.get("visibility") or {}).get("repr") or (metar.get("visibility") or {}).get("repr") or "Unknown"
        wx_codes = summary_metar.get("wx_codes") or metar.get("wx_codes") or []
        wx_parts = [
            str(code.get("value") or code.get("repr"))
            for code in wx_codes
            if isinstance(code, dict) and (code.get("value") or code.get("repr"))
        ]
        wx_text = ", ".join(wx_parts) if wx_parts else "None"
        embed.add_field(name="Current Conditions", value=f"**Flight Rules:** {rules}\n**Visibility:** {visibility}\n**Weather:** {wx_text}", inline=False)

        metar_summary = metar.get("summary") or self._truncate_report(metar.get("raw"), 500)
        if metar_summary:
            embed.add_field(name="METAR Summary", value=self._truncate_report(metar_summary, 1024), inline=False)

        taf_periods = summary_taf.get("forecast") or []
        if taf_periods:
            period_lines = []
            for period in taf_periods[:4]:
                start = self._short_dt(period.get("start_time"))
                end = self._short_dt(period.get("end_time"))
                rules = period.get("flight_rules") or "Unknown"
                period_lines.append(f"`{start}` → `{end}`: **{rules}**")
            embed.add_field(name="TAF Trend", value="\n".join(period_lines), inline=False)

        raw_taf = taf.get("raw")
        if raw_taf:
            embed.add_field(name="Raw TAF", value=self._truncate_report(raw_taf, 1024), inline=False)

    def _add_metar_fields(self, embed: discord.Embed, metar: dict):
        if not metar:
            embed.description = "No METAR data available for this station."
            return

        rules = metar.get("flight_rules") or "Unknown"
        wind = self._format_wind(metar)
        visibility = self._format_visibility(metar)
        temperature = self._format_temperature(metar)
        altimeter = self._format_altimeter(metar)
        clouds = self._format_clouds(metar.get("clouds") or [])
        wx_codes = self._format_wx_codes(metar.get("wx_codes") or [])

        embed.add_field(name="Observation", value=f"**Flight Rules:** {rules}\n**Wind:** {wind}\n**Visibility:** {visibility}\n**Altimeter:** {altimeter}", inline=False)
        embed.add_field(name="Temperature", value=temperature, inline=True)
        embed.add_field(name="Weather", value=wx_codes, inline=True)
        embed.add_field(name="Clouds", value=clouds, inline=False)

        report_time = self._short_dt((metar.get("time") or {}).get("dt"))
        if report_time:
            embed.add_field(name="Observed", value=report_time, inline=True)

        summary = metar.get("summary")
        if summary:
            embed.add_field(name="Summary", value=self._truncate_report(summary, 1024), inline=False)

        raw = metar.get("raw") or metar.get("sanitized")
        if raw:
            embed.add_field(name="Raw Report", value=self._truncate_report(raw, 1024), inline=False)

    def _add_taf_fields(self, embed: discord.Embed, taf: dict):
        if not taf:
            embed.description = "No TAF data available for this station."
            return

        start_time = self._short_dt((taf.get("start_time") or {}).get("dt"))
        end_time = self._short_dt((taf.get("end_time") or {}).get("dt"))
        if start_time or end_time:
            embed.add_field(name="Validity", value=f"`{start_time or 'Unknown'}` → `{end_time or 'Unknown'}`", inline=False)

        forecast_periods = taf.get("forecast") or []
        if forecast_periods:
            for index, period in enumerate(forecast_periods[:4], start=1):
                start = self._short_dt((period.get("start_time") or {}).get("dt"))
                end = self._short_dt((period.get("end_time") or {}).get("dt"))
                rules = period.get("flight_rules") or "Unknown"
                summary = period.get("summary") or self._truncate_report(period.get("raw"), 300) or "No summary available"
                embed.add_field(
                    name=f"Forecast {index}",
                    value=f"`{start or 'Unknown'}` → `{end or 'Unknown'}`\n**{rules}**\n{self._truncate_report(summary, 900)}",
                    inline=False,
                )

        raw = taf.get("raw") or taf.get("sanitized")
        if raw:
            embed.add_field(name="Raw TAF", value=self._truncate_report(raw, 1024), inline=False)

    @staticmethod
    def _truncate_report(text, limit):
        if not text:
            return None
        text = str(text)
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."

    @staticmethod
    def _short_dt(value):
        if not value:
            return None
        if "T" in value:
            return value.replace("T", " ").replace("+00:00Z", "Z").replace("+00:00", "Z")
        return value

    @staticmethod
    def _format_visibility(report):
        visibility = report.get("visibility") or {}
        repr_value = visibility.get("repr")
        units = (report.get("units") or {}).get("visibility") or "sm"
        if repr_value:
            return f"{repr_value} {units}"
        return "Unknown"

    @staticmethod
    def _format_wind(report):
        direction = (report.get("wind_direction") or {}).get("repr") or "VRB"
        speed = (report.get("wind_speed") or {}).get("repr") or "0"
        gust = (report.get("wind_gust") or {}).get("repr")
        units = (report.get("units") or {}).get("wind_speed") or "kt"
        base = f"{direction} at {speed}{units}"
        if gust:
            base += f" gusting {gust}{units}"
        return base

    @staticmethod
    def _format_temperature(report):
        temperature = (report.get("temperature") or {}).get("repr")
        dewpoint = (report.get("dewpoint") or {}).get("repr")
        units = (report.get("units") or {}).get("temperature") or "C"
        if temperature is None and dewpoint is None:
            return "Unknown"
        return f"{temperature if temperature is not None else '?'}{units} / {dewpoint if dewpoint is not None else '?'}{units}"

    @staticmethod
    def _format_altimeter(report):
        altimeter = report.get("altimeter") or {}
        repr_value = altimeter.get("repr")
        value = altimeter.get("value")
        units = (report.get("units") or {}).get("altimeter") or "inHg"
        if repr_value and value is not None:
            return f"{repr_value} ({value} {units})"
        if repr_value:
            return repr_value
        return "Unknown"

    @staticmethod
    def _format_clouds(clouds):
        if not clouds:
            return "None reported"
        parts = []
        for cloud in clouds[:5]:
            base = cloud.get("base")
            cloud_type = cloud.get("type") or cloud.get("repr") or "Cloud"
            if base is not None:
                parts.append(f"{cloud_type} {base}00ft")
            else:
                parts.append(cloud_type)
        return ", ".join(parts)

    @staticmethod
    def _format_wx_codes(wx_codes):
        if not wx_codes:
            return "None reported"
        parts = []
        for code in wx_codes:
            if isinstance(code, dict):
                parts.append(code.get("value") or code.get("repr") or "Unknown")
            else:
                parts.append(str(code))
        return ", ".join(parts)


def _clean_closure_reason(raw):
    """Clean and humanize closure reason text from FAA XML."""
    clean_msg = re.sub(r'^![A-Z0-9]{3,4}\s\d+/\d+\s[A-Z0-9]{3,4}\s', '', raw)
    clean_msg = re.sub(r'\s\d{10}-\d{10}$', '', clean_msg)
    clean_msg = (clean_msg.replace("AD AP CLSD TO NON SKED TRANSIENT GA ACFT EXC", "Closed to non-scheduled/private flights except")
                  .replace("PPR", "Prior Permission Required")
                  .replace("EXC", "except")
                  .strip())
    return clean_msg


@cog_i18n(_)
class AirportCommands:
    """Airport-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
        self.api = APIManager(cog)
        self.helpers = HelperUtils(cog)
        self.xml_parser = XMLParser()

    async def _avwx_fetch_bundle(self, station_code: str):
        """Fetch AVWX summary, METAR, and TAF data for a station."""
        station_code = station_code.upper().strip()

        summary_task = self.cog.api.get_avwx_summary(station_code)
        metar_task = self.cog.api.get_avwx_report("metar", station_code)
        taf_task = self.cog.api.get_avwx_report("taf", station_code)
        summary_result, metar_result, taf_result = await asyncio.gather(summary_task, metar_task, taf_task)

        summary, summary_error = summary_result
        metar, metar_error = metar_result
        taf, taf_error = taf_result

        if not any((summary, metar, taf)):
            errors = [msg for msg in (summary_error, metar_error, taf_error) if msg]
            return None, errors[0] if errors else f"No AVWX data available for {station_code}."

        return {
            "summary": summary,
            "metar": metar,
            "taf": taf,
        }, None

    async def _send_avwx_view(self, ctx, station_code: str, initial_filter: str = "overview"):
        """Fetch AVWX data and send the interactive report view."""
        station_code = station_code.upper().strip()
        reports, error = await self._avwx_fetch_bundle(station_code)
        if error:
            embed = discord.Embed(title="AVWX Unavailable", description=error, color=0xff4545)
            await ctx.send(embed=embed)
            return

        view = AVWXWeatherView(
            station_code=station_code,
            report_data=reports,
            airport_commands=self,
            initial_filter=initial_filter,
        )
        embed = view.build_embed(initial_filter)
        await ctx.send(embed=embed, view=view)

    async def avwx_conditions(self, ctx, station_code: str):
        """Show AVWX aviation weather overview for a station."""
        await self._send_avwx_view(ctx, station_code, initial_filter="overview")

    async def avwx_metar(self, ctx, station_code: str):
        """Show AVWX METAR for a station."""
        await self._send_avwx_view(ctx, station_code, initial_filter="metar")

    async def avwx_taf(self, ctx, station_code: str):
        """Show AVWX TAF for a station."""
        await self._send_avwx_view(ctx, station_code, initial_filter="taf")
    
    async def _faa_fetch_data(self, airport_code: Optional[str] = None):
        """Fetch and parse FAA airport status. Returns (ground_delays, arrival_departure_delays, closures, update_time) or None."""
        try:
            headers = {}
            user_agent = await self.cog.config.user_agent()
            if user_agent:
                headers["User-Agent"] = user_agent
            async with aiohttp.ClientSession() as session:
                root = await self.xml_parser.fetch_and_parse_xml(
                    session,
                    "https://nasstatus.faa.gov/api/airport-status-information",
                    headers if headers else None
                )
            if root is None:
                return None
            update_time = self.xml_parser.get_text(root, "Update_Time", "Unknown")
            ground_delays = []
            arrival_departure_delays = []
            closures = []
            ground_delay_list = root.find(".//Ground_Delay_List")
            if ground_delay_list is not None:
                for delay in ground_delay_list.findall(".//Ground_Delay"):
                    arpt = self.xml_parser.get_text(delay, "ARPT")
                    if not airport_code or arpt == airport_code.upper():
                        ground_delays.append({
                            'arpt': arpt,
                            'reason': self.xml_parser.get_text(delay, "Reason"),
                            'avg': self.xml_parser.get_text(delay, "Avg"),
                            'max': self.xml_parser.get_text(delay, "Max")
                        })
            arrival_departure_list = root.find(".//Arrival_Departure_Delay_List")
            if arrival_departure_list is not None:
                for delay in arrival_departure_list.findall(".//Delay"):
                    arpt = self.xml_parser.get_text(delay, "ARPT")
                    if not airport_code or arpt == airport_code.upper():
                        arr_dep = delay.find("Arrival_Departure")
                        if arr_dep is not None:
                            delay_type = arr_dep.get("Type", "Unknown")
                            arrival_departure_delays.append({
                                'arpt': arpt,
                                'reason': self.xml_parser.get_text(delay, "Reason"),
                                'type': delay_type,
                                'min': self.xml_parser.get_text(arr_dep, "Min"),
                                'max': self.xml_parser.get_text(arr_dep, "Max"),
                                'trend': self.xml_parser.get_text(arr_dep, "Trend")
                            })
            closure_list = root.find(".//Airport_Closure_List")
            if closure_list is not None:
                for airport in closure_list.findall(".//Airport"):
                    arpt = self.xml_parser.get_text(airport, "ARPT")
                    if not airport_code or arpt == airport_code.upper():
                        closures.append({
                            'arpt': arpt,
                            'reason': _clean_closure_reason(self.xml_parser.get_text(airport, "Reason")),
                            'start': self.xml_parser.get_text(airport, "Start"),
                            'reopen': self.xml_parser.get_text(airport, "Reopen")
                        })
            return (ground_delays, arrival_departure_delays, closures, update_time)
        except Exception:
            return None
    
    async def airport_info(self, ctx, airport_code: str):
        """Get airport information by ICAO or IATA code."""
        airport_code = airport_code.upper()
        
        # Try to get airport data
        airport_data = await self.helpers.get_airport_data(airport_code)
        
        if airport_data:
            embed = discord.Embed(title=f"Airport Information - {airport_code}", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            
            # Basic airport information
            name = airport_data.get('name', 'N/A')
            city = airport_data.get('city', 'N/A')
            country = airport_data.get('country', 'N/A')
            
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="City", value=city, inline=True)
            embed.add_field(name="Country", value=country, inline=True)
            
            # Coordinates
            lat = airport_data.get('latitude', 'N/A')
            lon = airport_data.get('longitude', 'N/A')
            if lat != 'N/A' and lon != 'N/A':
                embed.add_field(name="Coordinates", value=f"{lat}, {lon}", inline=False)
            
            # Elevation
            elevation = airport_data.get('elevation', 'N/A')
            if elevation != 'N/A':
                embed.add_field(name="Elevation", value=f"{elevation} ft", inline=True)
            
            # Timezone
            timezone = airport_data.get('timezone', 'N/A')
            if timezone != 'N/A':
                embed.add_field(name="Timezone", value=timezone, inline=True)
            
            # Get airport image
            image_url = await self.helpers.get_airport_image(lat, lon)
            if image_url:
                embed.set_image(url=image_url)
            
            # Add view with buttons
            view = discord.ui.View()
            if lat != 'N/A' and lon != 'N/A':
                google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                view.add_item(discord.ui.Button(label="View on Google Maps", emoji="🗺️", url=google_maps_url, style=discord.ButtonStyle.link))
            
            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(title="Airport Not Found", description=f"No airport found with code {airport_code}.", color=0xff4545)
            await ctx.send(embed=embed)

    async def runway_info(self, ctx, airport_code: str):
        """Get runway information for an airport."""
        airport_code = airport_code.upper()
        
        # Get runway data
        runway_data = await self.helpers.get_runway_data(airport_code)

        # Surface HTTP/errors from helper (includes redacted URL when available)
        if isinstance(runway_data, dict) and 'error' in runway_data:
            reason = runway_data.get('error') or 'Unknown error'
            url = runway_data.get('url')
            desc = f"Could not fetch runway information for {airport_code}.\nReason: {reason}"
            if url:
                desc += f"\nURL: {url}"
            await ctx.send(embed=discord.Embed(title="Runway Lookup Failed", description=desc, color=0xff4545))
            return
        
        if runway_data and runway_data.get('runways'):
            embed = discord.Embed(title=f"Runway Information - {airport_code}", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            
            runways = runway_data['runways']
            for runway in runways:
                runway_name = runway.get('name', 'N/A')
                length = runway.get('length', 'N/A')
                width = runway.get('width', 'N/A')
                surface = runway.get('surface', 'N/A')
                
                runway_info = f"**Length:** {length} ft\n"
                runway_info += f"**Width:** {width} ft\n"
                runway_info += f"**Surface:** {surface}"
                
                embed.add_field(name=f"Runway {runway_name}", value=runway_info, inline=False)
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="No Runway Data", description=f"No runway information found for {airport_code}.", color=0xff4545)
            await ctx.send(embed=embed)

    async def navaid_info(self, ctx, airport_code: str):
        """Get navigational aids for an airport."""
        airport_code = airport_code.upper()
        
        # Get navaid data
        navaid_data = await self.helpers.get_navaid_data(airport_code)

        # If helper returned None, treat as an unexpected error
        if navaid_data is None:
            await ctx.send(embed=discord.Embed(title="Navaid Lookup Failed", description=f"Could not fetch navaid information for {airport_code}.", color=0xff4545))
            return

        # If helper returned an error dict, surface the reason to the user
        if isinstance(navaid_data, dict) and 'error' in navaid_data:
            reason = navaid_data.get('error') or 'Unknown error'
            url = navaid_data.get('url')
            desc = f"Could not fetch navaid information for {airport_code}.\nReason: {reason}"
            if url:
                desc += f"\nURL: {url}"
            await ctx.send(embed=discord.Embed(title="Navaid Lookup Failed", description=desc, color=0xff4545))
            return

        navaids = navaid_data.get('navaids', []) or []
        if not navaids:
            await ctx.send(embed=discord.Embed(title="No Navaid Data", description=f"No navigational aid information found for {airport_code}.", color=0xff4545))
            return

        embed = discord.Embed(title=f"Navigational Aids - {airport_code}", color=0xfffffe)

        def _format_frequency(n):
            # Prefer common keys used by airportdb.io
            freq = n.get('frequency') or n.get('frequency_khz') or n.get('dme_frequency_khz') or n.get('dme_frequency')
            if not freq:
                return 'N/A'
            try:
                fstr = str(freq)
                # If looks like kHz integer (e.g. 115900), convert to MHz
                if fstr.isdigit() and len(fstr) >= 4:
                    mhz = float(fstr) / 1000.0
                    return f"{mhz:.3f} MHz"
                return fstr
            except Exception:
                return str(freq)

        for navaid in navaids:
            # Use ident if available as the concise label
            ident = navaid.get('ident') or navaid.get('filename') or navaid.get('name') or 'Unknown'
            frequency = _format_frequency(navaid)

            # Minimal field: ident -> frequency
            embed.add_field(name=ident, value=frequency, inline=True)

        await ctx.send(embed=embed)

    async def weather_forecast(self, ctx, airport_code: str):
        """Get weather forecast for an airport."""
        airport_code = airport_code.upper()
        
        # Get airport coordinates first
        airport_data = await self.helpers.get_airport_data(airport_code)
        
        if airport_data:
            lat = airport_data.get('latitude', 'N/A')
            lon = airport_data.get('longitude', 'N/A')
            
            if lat != 'N/A' and lon != 'N/A':
                # Get weather forecast
                weather_data = await self.helpers.get_weather_forecast(lat, lon)
                
                if weather_data:
                    embed = discord.Embed(title=f"Weather Forecast - {airport_code}", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    
                    # Current weather
                    current = weather_data.get('current', {})
                    if current:
                        temp = current.get('temp', 'N/A')
                        condition = current.get('condition', {}).get('text', 'N/A')
                        wind_speed = current.get('wind_kph', 'N/A')
                        humidity = current.get('humidity', 'N/A')
                        
                        embed.add_field(name="Current Weather", value=f"**Temperature:** {temp}°C\n**Condition:** {condition}\n**Wind:** {wind_speed} km/h\n**Humidity:** {humidity}%", inline=False)
                    
                    # Forecast
                    forecast = weather_data.get('forecast', {}).get('forecastday', [])
                    if forecast:
                        for day in forecast[:3]:  # Show next 3 days
                            date = day.get('date', 'N/A')
                            max_temp = day.get('day', {}).get('maxtemp_c', 'N/A')
                            min_temp = day.get('day', {}).get('mintemp_c', 'N/A')
                            condition = day.get('day', {}).get('condition', {}).get('text', 'N/A')
                            
                            day_info = f"**Max:** {max_temp}°C\n**Min:** {min_temp}°C\n**Condition:** {condition}"
                            embed.add_field(name=date, value=day_info, inline=True)
                    
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Weather Data Unavailable", description=f"Weather forecast data is not available for {airport_code}.", color=0xff4545)
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Invalid Coordinates", description=f"Could not get coordinates for {airport_code}.", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Airport Not Found", description=f"No airport found with code {airport_code}.", color=0xff4545)
            await ctx.send(embed=embed) 

    async def paginate_embed(self, ctx, embeds):
        await menu(ctx, embeds, DEFAULT_CONTROLS)

    async def forecast(self, ctx, code: str):
        code_type = 'icao' if len(code) == 4 else 'iata' if len(code) == 3 else None
        if not code_type:
            await ctx.send(embed=discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545))
            return

        try:
            # Include optional custom User-Agent (some APIs like api.weather.gov may require it)
            headers = {}
            user_agent = await self.cog.config.user_agent()
            if user_agent:
                headers["User-Agent"] = user_agent

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://airport-data.com/api/ap_info.json?{code_type}={code}",
                    headers=headers if headers else None,
                ) as response1:
                    data1 = await response1.json()
                    latitude, longitude = data1.get('latitude'), data1.get('longitude')
                    country_code = data1.get('country_code')
                    airport_name = data1.get('name')
                    if not latitude or not longitude:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch latitude and longitude for the provided code.", color=0xff4545))
                        return

                if country_code == 'US':
                    # US logic (NOAA/NWS)
                    async with session.get(
                        f"https://api.weather.gov/points/{latitude},{longitude}",
                        headers=headers if headers else None,
                    ) as response2:
                        data2 = await response2.json()
                        forecast_url = data2.get('properties', {}).get('forecast')
                        if not forecast_url:
                            await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast URL.", color=0xff4545))
                            return

                    async with session.get(forecast_url, headers=headers if headers else None) as response3:
                        data3 = await response3.json()
                        periods = data3.get('properties', {}).get('periods')
                        if not periods:
                            await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast details.", color=0xff4545))
                            return

                    combined_pages = []
                    for period in periods:
                        timeemoji = "☀️" if period.get('isDaytime') else "🌙"
                        description = f"{timeemoji} {period['name']}"
                        embed = discord.Embed(title=f"Weather forecast for {code.upper()}", description=description, color=0xfffffe)
                        temperature = period['temperature']
                        temperature_unit = period['temperatureUnit']
                        # Determine the emoji based on temperature
                        if temperature_unit == 'F':
                            if temperature >= 90:
                                emoji = '🔥'  # Hot
                            elif temperature <= 32:
                                emoji = '❄️'  # Cold
                            else:
                                emoji = '🌡️'  # Moderate
                        else:  # Assuming Celsius
                            if temperature >= 32:
                                emoji = '🔥'  # Hot
                            elif temperature <= 0:
                                emoji = '❄️'  # Cold
                            else:
                                emoji = '🌡️'  # Moderate
                        embed.add_field(name="Temperature", value=f"{emoji} **`{temperature}° {temperature_unit}`**", inline=True)
                        wind_speed = period['windSpeed']
                        wind_direction = period['windDirection']
                        # Determine the emoji based on wind speed
                        try:
                            speed_value = int(wind_speed.split()[0])
                            if speed_value >= 30:
                                wind_emoji = '💨'  # Strong wind
                            elif speed_value >= 15:
                                wind_emoji = '🌬️'  # Moderate wind
                            else:
                                wind_emoji = '🍃'  # Light wind
                        except ValueError:
                            wind_emoji = '🍃'  # Default to light wind if parsing fails
                        # Determine the emoji based on wind direction
                        direction_emoji = {
                            'N': '⬆️', 'NNE': '⬆️↗️', 'NE': '↗️', 'ENE': '↗️➡️', 'E': '➡️', 'ESE': '➡️↘️', 'SE': '↘️',
                            'SSE': '↘️⬇️', 'S': '⬇️', 'SSW': '⬇️↙️', 'SW': '↙️', 'WSW': '↙️⬅️', 'W': '⬅️',
                            'WNW': '⬅️↖️', 'NW': '↖️', 'NNW': '↖️⬆️'
                        }.get(wind_direction, '❓')
                        embed.add_field(name="Wind speed", value=f"{wind_emoji} **`{wind_speed}`**", inline=True)
                        embed.add_field(name="Wind direction", value=f"{direction_emoji} **`{wind_direction}`**", inline=True)
                        if 'relativeHumidity' in period and period['relativeHumidity']['value'] is not None:
                            embed.add_field(name="Humidity", value=f"**`{period['relativeHumidity']['value']}%`**", inline=True)
                        if 'probabilityOfPrecipitation' in period and period['probabilityOfPrecipitation']['value'] is not None:
                            embed.add_field(name="Chance of precipitation", value=f"**`{period['probabilityOfPrecipitation']['value']}%`**", inline=True)
                        if 'dewpoint' in period and period['dewpoint']['value'] is not None:
                            dewpoint_celsius = period['dewpoint']['value']
                            dewpoint_fahrenheit = (dewpoint_celsius * 9/5) + 32
                            embed.add_field(name="Dewpoint", value=f"**`{dewpoint_fahrenheit:.1f}°F`**", inline=True)
                        embed.add_field(name="Forecast", value=f"**`{period['detailedForecast']}`**", inline=False)
                        combined_pages.append(embed)
                    await self.paginate_embed(ctx, combined_pages)
                else:
                    # Non-US logic (OpenWeatherMap)
                    data = await self.cog.api.get_openweathermap_forecast(latitude, longitude)
                    if not data or 'list' not in data:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast from OpenWeatherMap.", color=0xff4545))
                        return
                    city = data.get('city', {}).get('name', code.upper())
                    country = data.get('city', {}).get('country', '')
                    combined_pages = []
                    for entry in data['list']:
                        dt_txt = entry.get('dt_txt', '')
                        main = entry.get('main', {})
                        weather = entry.get('weather', [{}])[0]
                        wind = entry.get('wind', {})
                        temp = main.get('temp')
                        feels_like = main.get('feels_like')
                        humidity = main.get('humidity')
                        description = weather.get('description', '').capitalize()
                        icon = weather.get('icon', '')
                        wind_speed = wind.get('speed')
                        wind_deg = wind.get('deg')
                        # Emoji logic for temperature
                        if temp is not None:
                            if temp >= 32:
                                emoji = '🔥'
                            elif temp <= 0:
                                emoji = '❄️'
                            else:
                                emoji = '🌡️'
                        else:
                            emoji = '🌡️'
                        # Wind speed emoji
                        try:
                            speed_value = float(wind_speed) if wind_speed is not None else 0
                            if speed_value >= 13.4:  # ~30 mph
                                wind_emoji = '💨'
                            elif speed_value >= 6.7:  # ~15 mph
                                wind_emoji = '🌬️'
                            else:
                                wind_emoji = '🍃'
                        except Exception:
                            wind_emoji = '🍃'
                        # Wind direction emoji
                        def deg_to_compass(deg):
                            if deg is None:
                                return '❓'
                            dirs = ['⬆️', '⬆️↗️', '↗️', '↗️➡️', '➡️', '➡️↘️', '↘️', '↘️⬇️', '⬇️', '⬇️↙️', '↙️', '↙️⬅️', '⬅️', '⬅️↖️', '↖️', '↖️⬆️']
                            ix = int((float(deg) + 11.25) / 22.5) % 16
                            return dirs[ix]
                        direction_emoji = deg_to_compass(wind_deg)
                        embed = discord.Embed(
                            title=f"Weather forecast for {airport_name or code.upper()}",
                            description=dt_txt,
                            color=0xfffffe
                        )
                        if icon:
                            embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{icon}@2x.png")
                        embed.add_field(name="Description", value=description, inline=False)
                        embed.add_field(name="Temperature", value=f"{emoji} **`{temp}°C (feels like {feels_like}°C)`**", inline=True)
                        embed.add_field(name="Wind speed", value=f"{wind_emoji} **`{wind_speed} m/s`**", inline=True)
                        embed.add_field(name="Wind direction", value=f"{direction_emoji} **`{wind_deg}°`**", inline=True)
                        embed.add_field(name="Humidity", value=f"**`{humidity}%`**", inline=True)
                        embed.add_field(name="Forecast", value=f"**`{description}`**", inline=False)
                        combined_pages.append(embed)
                    await self.paginate_embed(ctx, combined_pages)
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Error", description=str(e), color=0xff4545)) 

    @commands.is_owner()
    @commands.command(name="setowmkey")
    async def setowmkey(self, ctx, api_key: str):
        """Set the OpenWeatherMap API key."""
        await self.cog.config.openweathermap_api.set(api_key)
        await ctx.send("OpenWeatherMap API key set.")

    @commands.is_owner()
    @commands.command(name="owmkey")
    async def owmkey(self, ctx):
        """Show the current OpenWeatherMap API key (partially masked)."""
        key = await self.cog.config.openweathermap_api()
        if key:
            await ctx.send(f"OpenWeatherMap API key: `{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}`")
        else:
            await ctx.send("No OpenWeatherMap API key set.")

    @commands.is_owner()
    @commands.command(name="clearowmkey")
    async def clearowmkey(self, ctx):
        """Clear the OpenWeatherMap API key."""
        await self.cog.config.openweathermap_api.set(None)
        await ctx.send("OpenWeatherMap API key cleared.")

    async def faa_status(self, ctx, airport_code: Optional[str] = None):
        """Get FAA National Airspace Status for airports with delays or closures.
        
        If airport_code is provided, filters to that specific airport (e.g., 'SAN' or 'LAS').
        If not provided, shows all airports with active delays/closures.
        """
        try:
            result = await self._faa_fetch_data(airport_code)
            if result is None:
                await ctx.send("❌ FAA API Unavailable.")
                return
            ground_delays, arrival_departure_delays, closures, update_time = result
            total_items = len(ground_delays) + len(arrival_departure_delays) + len(closures)
            if total_items == 0:
                embed = discord.Embed(
                    description="✅ No active delays or closures reported.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            view = FAAStatusView(
                ground_delays=ground_delays,
                arrival_departure_delays=arrival_departure_delays,
                closures=closures,
                update_time=update_time,
                airport_code=airport_code,
                airport_commands=self
            )
            embed = view.build_embed("all")
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to fetch FAA status: {str(e)}",
                color=0xff4545
            )
            await ctx.send(embed=embed) 
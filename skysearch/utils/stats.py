import discord
import json
import urllib.parse
import datetime
import time


def _quickchart_url(chart_config: dict, width: int, height: int) -> str:
    config_json = json.dumps(chart_config, separators=(",", ":"))
    return (
        "https://quickchart.io/chart?"
        + f"width={width}&height={height}&format=png&backgroundColor=transparent&devicePixelRatio=2&c="
        + urllib.parse.quote(config_json)
    )


def build_stats_embed(api_stats: dict) -> discord.Embed:
    embed = discord.Embed(
        title="📊 Airplanes.live API Statistics",
        description="Detailed request tracking and performance metrics",
        color=0x00FF00,
    )

    embed.add_field(
        name="📈 Overall Stats",
        value=(
            f"**Total Requests:** {api_stats['total_requests']:,}\n"
            f"**Success Rate:** {api_stats['success_rate']:.1f}%\n"
            f"**Last Request:** {api_stats.get('last_request_time_formatted', 'Never')}"
        ),
        inline=True,
    )

    embed.add_field(
        name="✅ Success/Failure",
        value=(
            f"**Successful:** {api_stats['successful_requests']:,}\n"
            f"**Failed:** {api_stats['failed_requests']:,}\n"
            f"**Rate Limited:** {api_stats['rate_limited_requests']:,}"
        ),
        inline=True,
    )

    embed.add_field(
        name="🌐 API Mode Usage",
        value=(
            f"**Primary:** {api_stats['api_mode_usage']['primary']:,}\n"
            f"**Fallback:** {api_stats['api_mode_usage']['fallback']:,}"
        ),
        inline=True,
    )

    if api_stats.get("avg_response_time", 0) > 0:
        embed.add_field(
            name="⚡ Performance",
            value=(
                f"**Avg Response:** {api_stats['avg_response_time']:.3f}s\n"
                f"**Last 24h:** {api_stats['requests_last_24h']:,} requests"
            ),
            inline=True,
        )

    endpoint_usage = api_stats.get("endpoint_usage") or {}
    if endpoint_usage:
        top_endpoints = sorted(endpoint_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        endpoint_text = "\n".join([f"**{endpoint}:** {count:,}" for endpoint, count in top_endpoints])
        embed.add_field(name="🔗 Top Endpoints", value=endpoint_text, inline=False)

    if api_stats.get("auth_failed_requests", 0) > 0 or api_stats.get("permission_denied_requests", 0) > 0:
        error_parts = []
        if api_stats.get("auth_failed_requests", 0) > 0:
            error_parts.append(f"**Auth Failed:** {api_stats['auth_failed_requests']:,}")
        if api_stats.get("permission_denied_requests", 0) > 0:
            error_parts.append(f"**Permission Denied:** {api_stats['permission_denied_requests']:,}")
        embed.add_field(name="⚠️ Error Details", value="\n".join(error_parts), inline=True)

    embed.set_footer(text="Use 'skysearch apistats_reset' to reset statistics | 'skysearch apistats_save' to manually save.")
    return embed


def build_stats_charts(api_stats: dict) -> list[discord.Embed]:
    chart_embeds: list[discord.Embed] = []

    # Success vs Failure pie
    try:
        total_success = int(api_stats.get("successful_requests", 0))
        total_failed = int(api_stats.get("failed_requests", 0))
        if (total_success + total_failed) > 0:
            chart = {
                "type": "pie",
                "data": {
                    "labels": ["Successful", "Failed"],
                    "datasets": [{
                        "data": [total_success, total_failed],
                        "backgroundColor": ["#2ecc71", "#e74c3c"],
                    }],
                },
                "options": {"plugins": {"legend": {"position": "bottom"}}},
            }
            url = _quickchart_url(chart, 600, 300)
            e = discord.Embed(title="Success vs Failure")
            e.set_image(url=url)
            chart_embeds.append(e)
    except Exception:
        pass

    # API mode usage doughnut
    try:
        mode_primary = int(api_stats.get("api_mode_usage", {}).get("primary", 0))
        mode_fallback = int(api_stats.get("api_mode_usage", {}).get("fallback", 0))
        if (mode_primary + mode_fallback) > 0:
            chart = {
                "type": "doughnut",
                "data": {
                    "labels": ["Primary", "Fallback"],
                    "datasets": [{
                        "data": [mode_primary, mode_fallback],
                        "backgroundColor": ["#3498db", "#9b59b6"],
                    }],
                },
                "options": {"plugins": {"legend": {"position": "bottom"}}},
            }
            url = _quickchart_url(chart, 600, 300)
            e = discord.Embed(title="API Mode Usage")
            e.set_image(url=url)
            chart_embeds.append(e)
    except Exception:
        pass

    # Top endpoints bar
    try:
        endpoint_usage = api_stats.get("endpoint_usage", {}) or {}
        if endpoint_usage:
            top_items = sorted(endpoint_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            labels = [k for k, _ in top_items]
            data_vals = [int(v) for _, v in top_items]
            chart = {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Requests",
                        "data": data_vals,
                        "backgroundColor": "#f1c40f",
                    }],
                },
                "options": {
                    "indexAxis": "y",
                    "plugins": {"legend": {"display": False}},
                    "scales": {"x": {"beginAtZero": True}},
                },
            }
            url = _quickchart_url(chart, 800, 300)
            e = discord.Embed(title="Top Endpoints")
            e.set_image(url=url)
            chart_embeds.append(e)
    except Exception:
        pass

    # Hourly requests line
    try:
        hourly = api_stats.get("hourly_requests", {}) or {}
        current_hour = int(time.time() // 3600)
        hours = [current_hour - i for i in reversed(range(24))]
        labels = [datetime.datetime.fromtimestamp(h * 3600).strftime("%H:%M") for h in hours]
        data_vals = [int(hourly.get(h, 0)) for h in hours]
        if any(v > 0 for v in data_vals):
            chart = {
                "type": "line",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Requests per hour",
                        "data": data_vals,
                        "fill": False,
                        "borderColor": "#1abc9c",
                        "tension": 0.3,
                    }],
                },
                "options": {
                    "plugins": {"legend": {"position": "bottom"}},
                    "scales": {"y": {"beginAtZero": True}},
                },
            }
            url = _quickchart_url(chart, 800, 300)
            e = discord.Embed(title="Hourly Requests (last 24h)")
            e.set_image(url=url)
            chart_embeds.append(e)
    except Exception:
        pass

    # Total requests per day bar
    try:
        daily = api_stats.get("daily_requests", {}) or {}
        current_day = int(time.time() // 86400)
        days = [current_day - i for i in reversed(range(30))]
        labels = [datetime.datetime.fromtimestamp(d * 86400).strftime("%b %d") for d in days]
        data_vals = [int(daily.get(d, 0)) for d in days]
        if any(v > 0 for v in data_vals):
            chart = {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Total requests per day",
                        "data": data_vals,
                        "backgroundColor": "#2c3e50",
                    }],
                },
                "options": {
                    "plugins": {"legend": {"display": False}},
                    "scales": {"y": {"beginAtZero": True}},
                },
            }
            url = _quickchart_url(chart, 800, 300)
            e = discord.Embed(title="Total Requests (last 30 days)")
            e.set_image(url=url)
            chart_embeds.append(e)
    except Exception:
        pass

    return chart_embeds


def build_stats_config_embed(save_config: dict) -> discord.Embed:
    embed = discord.Embed(
        title="⚙️ API Statistics Save Configuration",
        description="Current configuration for automatic saving of API statistics",
        color=0x00AAFF,
    )
    embed.add_field(
        name="📊 Batch Saving",
        value=(
            f"**Batch Size:** {save_config['batch_size']} requests\n"
            f"**Current Count:** {save_config['requests_since_last_save']} requests"
        ),
        inline=True,
    )
    embed.add_field(
        name="⏰ Time-Based Saving",
        value=(
            f"**Interval:** {save_config['time_interval']} seconds\n"
            f"**Time Since Last Save:** {save_config['seconds_since_last_save']:.1f} seconds"
        ),
        inline=True,
    )
    embed.add_field(
        name="🔄 Save Strategy",
        value=(
            "**Hybrid Approach:** Save when either:\n"
            "• Batch size is reached (10 requests)\n"
            "• Time interval is reached (30 seconds)\n"
            "• Whichever comes first"
        ),
        inline=False,
    )
    embed.set_footer(text="This prevents config spam while ensuring data persistence")
    return embed



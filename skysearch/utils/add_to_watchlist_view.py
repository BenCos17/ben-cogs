"""
Add to Watchlist button view for aircraft embeds
"""

import discord
from urllib.parse import quote_plus

from redbot.core.i18n import Translator

_ = Translator("Skysearch", __file__)


class AddToWatchlistView(discord.ui.View):
    """View with aircraft link buttons and Add to Watchlist button."""

    def __init__(self, cog, aircraft_data, *, include_watchlist=True, timeout=300):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.aircraft_data = aircraft_data
        icao = (aircraft_data.get("hex", "") or "").upper()
        if not icao:
            include_watchlist = False

        # Link buttons
        link = f"https://globe.airplanes.live/?icao={icao}"
        self.add_item(
            discord.ui.Button(label="View on airplanes.live", emoji="🗺️", url=link, style=discord.ButtonStyle.link)
        )

        # Social media buttons
        ground_speed_knots = aircraft_data.get("gs") or aircraft_data.get("ground_speed")
        ground_speed_mph = "unknown"
        if ground_speed_knots is not None and ground_speed_knots != "N/A":
            try:
                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)
            except (ValueError, TypeError):
                pass

        lat = aircraft_data.get("lat", "N/A")
        lon = aircraft_data.get("lon", "N/A")
        if lat not in ("N/A", None):
            try:
                lat_f = round(float(lat), 2)
                lat_dir = "N" if lat_f >= 0 else "S"
                lat = f"{abs(lat_f)}{lat_dir}"
            except (ValueError, TypeError):
                pass
        if lon not in ("N/A", None):
            try:
                lon_f = round(float(lon), 2)
                lon_dir = "E" if lon_f >= 0 else "W"
                lon = f"{abs(lon_f)}{lon_dir}"
            except (ValueError, TypeError):
                pass

        squawk_code = aircraft_data.get("squawk", "N/A")
        emergency_squawk_codes = ["7500", "7600", "7700"]
        if squawk_code in emergency_squawk_codes:
            tweet_text = f"Spotted an aircraft declaring an emergency! #Squawk #{squawk_code}, flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. #SkySearch #Emergency\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
        else:
            tweet_text = f"Tracking flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph using #SkySearch\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
        tweet_url = f"https://x.com/intent/tweet?text={quote_plus(tweet_text)}"
        self.add_item(discord.ui.Button(label="Post on X", emoji="📣", url=tweet_url, style=discord.ButtonStyle.link))

        whatsapp_text = f"Check out this aircraft! Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. Track live @ https://globe.airplanes.live/?icao={icao} #SkySearch"
        whatsapp_url = f"https://api.whatsapp.com/send?text={quote_plus(whatsapp_text)}"
        self.add_item(discord.ui.Button(label="Send on WhatsApp", emoji="📱", url=whatsapp_url, style=discord.ButtonStyle.link))

        # Add to Watchlist button (interactive)
        if include_watchlist and icao:
            self.add_item(AddToWatchlistButton(cog=cog, icao=icao))


class AddToWatchlistButton(discord.ui.Button):
    """Button that adds aircraft to the user's watchlist when clicked."""

    def __init__(self, *, cog, icao: str):
        super().__init__(
            label=_("Add to Watchlist"),
            emoji="➕",
            style=discord.ButtonStyle.secondary,
            custom_id=None,  # Ephemeral views don't need custom_id
        )
        self.cog = cog
        self.icao = icao

    async def callback(self, interaction: discord.Interaction):
        """Handle button click - add aircraft to user's watchlist."""
        user = interaction.user
        user_config = self.cog.config.user(user)

        # Validate ICAO
        is_valid, error_msg = self.cog.helpers.validate_icao(self.icao)
        if not is_valid:
            await interaction.response.send_message(
                _("❌ Invalid ICAO: {error}").format(error=error_msg),
                ephemeral=True,
            )
            return

        watchlist = await user_config.watchlist()

        if self.icao in watchlist:
            await interaction.response.send_message(
                _("**{icao}** is already in your watchlist.").format(icao=self.icao),
                ephemeral=True,
            )
            return

        watchlist.append(self.icao)
        await user_config.watchlist.set(watchlist)

        # Initialize aircraft state
        aircraft_state = await user_config.watchlist_aircraft_state()
        aircraft_state[self.icao] = "unknown"
        await user_config.watchlist_aircraft_state.set(aircraft_state)

        await interaction.response.send_message(
            _("✅ Added **{icao}** to your watchlist. You'll be notified when it comes online, takes off, or lands.").format(
                icao=self.icao
            ),
            ephemeral=True,
        )

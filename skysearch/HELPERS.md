# SkySearch Helper and Utility Reference

This file explains what the main support modules in SkySearch do and how they fit together.

These modules are not user-facing commands by themselves. Instead, they provide shared logic used by the aircraft, airport, alerts, and stats features.

---

## `utils/helpers.py` — `HelperUtils`

This is the largest and most important helper module in the project.

### Main purpose
`HelperUtils` handles the glue work between raw aircraft/airport data and the Discord embed UI. It formats data for display, fetches images, checks JSON safety, and prepares feeder data for use in commands.

### Key responsibilities
- Attach a default airplane image when a lookup has no photo.
- Send embeds with a thumbnail fallback automatically.
- Validate feeder URLs and restrict them to allowed HTTPS domains.
- Fetch and normalize aircraft photos from Planespotters.
- Build aircraft info embeds with details such as:
  - callsign
  - registration
  - ICAO hex
  - altitude
  - heading
  - position
  - squawk code
  - aircraft model
  - speed
  - category
  - flight status
  - intelligence tags (military, police, emergency, etc.)
- Lookup airport information, airport images, runway data, and navaid data.
- Parse JSON input from a URL or raw text for feeder data.
- Create feeder embeds and feeder UI buttons.
- Format common aviation values for nicer display.

### Important methods
- `get_default_airplane_file()`
  - Returns the local default airplane image as a Discord file if it exists.

- `send_embed_with_default_thumbnail()`
  - Sends an embed and automatically attaches the default aircraft image when the embed is using the fallback thumbnail.

- `_ensure_http_client()`
  - Ensures the cog has a reusable `aiohttp.ClientSession`.

- `_get_allowed_feeder_domains()`
  - Returns the list of approved domains that JSON feeder URLs can come from.

- `_is_allowed_feeder_url()`
  - Allows only HTTPS URLs from approved domains.

- `_get_photo_url()`
  - Picks the best usable image URL from a Planespotters photo payload.

- `_get_planespotters_photo()`
  - Requests and normalizes the first usable aircraft photo.

- `_get_http_headers()`
  - Returns request headers with the configured User-Agent, including Planespotters-specific overrides if set.

- `get_photo_by_hex()`
  - Attempts to find a photo using a hex code, then falls back to registration or aircraft data lookup.

- `get_photo_by_aircraft_data()`
  - Convenience version that pulls the photo from a full aircraft record.

- `create_aircraft_embed()`
  - Builds the standard embed used for aircraft lookup results.

- `get_airport_data()`
  - Requests airport metadata from airport-data.com.

- `get_airport_image()`
  - Builds an OpenStreetMap static image URL for an airport.

- `get_runway_data()`
  - Fetches runway records from airportdb.io.

- `get_navaid_data()`
  - Fetches navigational aids for an airport.

- `parse_json_input()`
  - Accepts a raw JSON string or a URL pointing to JSON and validates it.

- `create_feeder_embed()`
  - Formats feeder JSON into a compact Discord embed summary.

- `create_feeder_view()`
  - Creates a view with buttons such as “View on Globe” and raw JSON links.

- `format_altitude()`, `format_speed()`, `format_position()`
  - Standardize values so they display cleanly in Discord.

---

## `utils/api.py` — `APIManager`

This module handles all the bot’s outbound API behavior.

### Main purpose
`APIManager` is the HTTP and request-tracking layer for SkySearch. It chooses API endpoints, supplies headers, and records how the bot is using upstream services.

### Key responsibilities
- Select primary or fallback airplanes.live URLs.
- Attach the required API key for the main API where appropriate.
- Track request counts, success/failure stats, rate limits, and auth failures.
- Count usage by API mode and endpoint.
- Save statistics back to the bot config.
- Manage AVWX headers for weather services.

### Important methods
- `get_api_url()`
  - Returns the active planes API URL.

- `get_primary_api_url()` / `get_fallback_api_url()`
  - Return the configured service URLs directly.

- `get_headers()`
  - Adds user-agent and auth information to requests.

- `get_avwx_headers()`
  - Returns the correct headers for AVWX requests.

- `_update_request_stats()`
  - Records total requests, success/failure, endpoint usage, and response time.

- `_extract_endpoint()`
  - Converts a URL into a cleaner endpoint label for statistics.

- `_save_stats_to_config()`
  - Persists stats to Red-DiscordBot config storage.

### Why it matters
This is the layer responsible for monitoring API health and making sure the bot can recover from fallback endpoints or throttling.

---

## `utils/export.py` — `ExportManager`

This module handles downloadable aircraft exports.

### Main purpose
`ExportManager` converts search results into shareable files the user can open outside Discord.

### Supported formats
- CSV
- PDF
- TXT
- HTML

### Important methods
- `export_aircraft_data()`
  - Builds the file name, chooses the format, and triggers the correct export writer.

- `_export_csv()`
  - Writes aircraft data as comma-separated rows.

- `_export_pdf()`
  - Creates a PDF with a compact summary table using reportlab.

- `_export_txt()`
  - Creates a plain-text export of all the fields.

- `_export_html()`
  - Generates a simple HTML table for browser viewing.

### Typical use
Aircraft lookup commands can return a file attachment so a user can save or inspect a large result set outside Discord.

---

## `utils/stats.py`

This module turns raw API stats into the embeds and charts shown in the bot’s statistics commands.

### Main functions
- `_quickchart_url()`
  - Encodes a chart config into a QuickChart URL.

- `_normalize_history()`
  - Converts stored time keys into a consistent integer-based lookup dictionary.

- `build_stats_embed()`
  - Produces the main “API statistics” embed.

- `build_stats_charts()`
  - Produces pie, doughnut, bar, and line chart embeds for different metrics.

### What it shows
- total requests
- success/failure counts
- rate limit info
- API mode usage (primary vs fallback)
- top endpoints
- hourly request trends
- selected performance metrics

---

## `utils/xml_parser.py` — `XMLParser`

This is a lightweight XML parsing utility used for XML-based API responses.

### Main purpose
When upstream data is returned as XML instead of JSON, this helper safely turns it into structured Python objects and makes it easy to query values.

### Important methods
- `parse_xml_string()`
  - Converts XML text to an `ElementTree` element.

- `find_elements()`
  - Finds matching child nodes under a given root.

- `get_text()`
  - Pulls text from a named child tag and falls back to a default value when missing.

- `fetch_and_parse_xml()`
  - Async-fetches XML from a URL and parses it immediately.

### Why it exists
It gives the bot a safe, simple parser for XML APIs without forcing the rest of the code to handle low-level XML parsing details.

---

## `utils/add_to_watchlist_view.py`

This file adds quick-action buttons to aircraft embeds.

### Main purpose
It gives users easy UI actions without needing separate commands for every action.

### Included actions
- “View on airplanes.live”
- “Post on X”
- “Send on WhatsApp”
- “Add to Watchlist”
- “Remove from Watchlist”

### Important classes
- `AddToWatchlistView`
  - Creates the whole interactive view.

- `AddToWatchlistButton`
  - Adds the aircraft to the user’s watchlist.

- `RemoveFromWatchlistButton`
  - Removes the aircraft from the user’s watchlist.

This is a convenience layer that improves the UX of lookup results and watchlist management.

---

## `utils/__init__.py`

This file is a short summary of the utility modules and acts as a simple package index for the utilities package.

---

## How the utilities work together

The best way to understand this package is to think of it as a pipeline:

1. A command or cog feature starts a request.
2. `APIManager` fetches raw data from the upstream service.
3. `HelperUtils` cleans and enriches that data for display.
4. The output is wrapped in a Discord embed, a button view, or an export file.
5. Stats and monitoring are recorded so the bot can spot failures or slow endpoints.

### End-to-end aircraft lookup flow

A normal aircraft lookup usually works like this:

```text
User runs command
    -> Skysearch cog decides which lookup to do
    -> APIManager calls airplanes.live
    -> raw aircraft dict comes back
    -> HelperUtils normalizes fields and builds an embed
    -> get_photo_by_hex() may fetch a Planespotters image
    -> create_aircraft_embed() adds details like altitude, heading, callsign, position, squawk, and status
    -> AddToWatchlistView adds action buttons
    -> final embed is sent to Discord
```

This is why `HelperUtils` is the busiest module: it takes raw API data and turns it into something the user can read quickly.

### Airport and weather flow

Airport data uses a slightly different path:

```text
User requests airport info
    -> HelperUtils.get_airport_data()
    -> airport-data.com or other metadata source is queried
    -> HelperUtils.get_airport_image() builds a static map URL
    -> runway/navaid functions fetch additional airport-specific data
    -> embed is assembled with airport details and links
```

The airport side is more about enrichment than raw flight tracking, but the same pattern still applies: fetch data, normalize it, render the response.

### Feeder JSON flow


```text
User provides JSON URL or raw JSON text
    -> HelperUtils.parse_json_input()
    -> checks HTTPS + allowed domain list
    -> reads content with a bounded size limit
    -> JSON is decoded and validated
    -> create_feeder_embed() builds a concise summary
    -> create_feeder_view() adds button links for map and raw data
```


### Watchlist interaction flow


```text
Aircraft result is displayed
    -> AddToWatchlistView creates action buttons
    -> user clicks Add to Watchlist
    -> AddToWatchlistButton validates ICAO
    -> helper watchlist functions update the saved user config
    -> user receives confirmation and later notifications via the watchlist task
```


### Stats and monitoring flow

The stats layer sits alongside the rest of the utilities:

```text
API request is executed
    -> APIManager._update_request_stats() records it
    -> endpoint, timer, mode, success/failure are captured
    -> stats.py builds summarizing embeds and chart URLs
    -> apistats commands show the results to the bot owner
```

This gives administrators visibility into which endpoints are being used and whether the bot is healthy.

### The bigger picture

The package is organized like this:

- `APIManager` = network layer
- `HelperUtils` = formatting and enrichment layer
- `ExportManager` = output/file layer
- `stats.py` = reporting/visualization layer
- `XMLParser` = XML parsing fallback
- `AddToWatchlistView` = interactive Discord UX layer


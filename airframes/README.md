# Airframes Cog for Red-DiscordBot

Integrates the Airframes REST API into Red-DiscordBot and exposes a
small set of owner-safe commands to query airframes, airlines, airports,
flights, messages and stations.

Quick summary
- Cog file: `airframes/airframes.py`
- Install metadata: `airframes/info.json`

Requirements
- Red-DiscordBot (no hard version limits in `info.json`)
- Python dependency: `aiohttp` (listed in `info.json`)

Installation
```text
[p]repo add ben-cogs https://github.com/bencos/ben-cogs
[p]cog install ben-cogs airframes
```

Configuration

- Set API base URL (owner-only):

```text
[p]airframes set base https://api.airframes.io/v1
```

- Set the API key (owner-only):

```text
[p]airframes set key YOUR_API_KEY_HERE
```

Commands

- `[p]airframes search [tail] [limit] [page]` — Search airframes. Examples:
	- `[p]airframes search` — first page of results
	- `[p]airframes search N12345` — filter by tail

- `[p]airframes get <id>` — Get a single airframe by integer/string `id`.
- `[p]airlines search` — List airlines.
- `[p]airports search` — List airports.
- `[p]flights active [query]` — List currently active flights (optional query).
- `[p]messages get <id>` — Get a message by id.
- `[p]stations list` — List known stations.

Behavior & notes
- Responses are posted as JSON code blocks and are truncated if they
	approach Discord message size limits (keeps output readable).
- The `set key` command stores the API key in Red's persistent config. Keys
	are never printed back to chat by the cog.
- Owner-only protection: Both `set base` and `set key` are restricted with
	`commands.is_owner()`.

Development

- Run a quick syntax check locally:

```powershell
python -m pyflakes airframes/airframes.py
python -m pyflakes airframes/__init__.py
```

- To test the cog interactively, run inside Red's Python environment and
	load the cog; or use a small test harness that imports `airframes.Airframes`
	and exercises `_request` with a mock session.





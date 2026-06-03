# Airframes Cog for Red-DiscordBot

Provides simple commands to query the Airframes REST API.

Installation


Basic setup (owner-only):

```
[p]airframes set base https://api.airframes.io/v1
[p]airframes set key <YOUR_API_KEY>
```

Commands

- `[p]airframes search [tail]` — search airframes, optional tail filter
- `[p]airframes get <id>` — get airframe by id
- `[p]airlines search` — list airlines
- `[p]airports search` — list airports
- `[p]flights active [query]` — list active flights
- `[p]messages get <id>` — get message by id
- `[p]stations list` — list stations

Notes

- The cog uses the `X-API-KEY` header when an API key is set.
- Results are returned as JSON blocks truncated to keep message length reasonable.

Counter cog

Commands:
- `counter create <name> [scope] [initial]` - Create a counter. scope is one of `guild` (default), `user`, `global`.
- `counter inc <name> [amount] [scope]` - Increment a counter by amount (default 1).
- `counter dec <name> [amount] [scope]` - Decrement a counter by amount (default 1).
- `counter set <name> <value> [scope]` - Set the counter to a specific integer value.
- `counter delete <name> [scope]` - Delete a counter.
- `counter show <name> [scope]` - Show the value of a counter.
- `counter list [scope]` - List counters in the given scope (default `guild`).

Notes:
- `guild` scope stores counters per-server and now allows multiple counters with the same name; each guild counter has a unique numeric id.
- When multiple guild counters share the same name, use the id to disambiguate (e.g., `counter inc 23 1`).
- `user` scope stores counters per-user (only visible to that user when listed with user scope).
- `global` scope requires the bot owner to create/modify/delete.

Examples:
- `counter create donuts` -> Creates `donuts` in the current server with value 0 and returns an id.
- `counter create coins` -> Creates a guild counter named `coins` (id shows in the response) — you can create another `coins` for another user.
- `counter create coins owner:@member` -> Create `coins` associated with a member (use a mention or ID); the requested owner will be asked for permission **in the server channel** (they will be pinged). If they accept via the Accept button or `counter owner accept <id>`, the counter is created and assigned to them; if they decline the request is removed.
- `counter owner list` -> Show pending owner requests addressed to you in this guild.
- `counter owner accept <request_id>` -> Accept a pending owner request (alternatively use the Accept button in the server message).
- `counter owner decline <request_id>` -> Decline a pending owner request.
- `counter inc 23 2` -> Add 2 to the counter with id `23`.
- `counter create wins user 0` -> Creates a user-scoped counter for the calling user.

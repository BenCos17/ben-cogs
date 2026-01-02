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
- `guild` scope stores counters per-server.
- `user` scope stores counters per-user (only visible to that user when listed with user scope).
- `global` scope requires the bot owner to create/modify/delete.

Examples:
- `counter create donuts` -> Creates `donuts` in the current server with value 0.
- `counter inc donuts 2` -> Adds 2 to the `donuts` counter in the server.
- `counter create wins user 0` -> Creates a user-scoped counter for the calling user.

# bloodontheclocktower

A Red-DiscordBot cog for running a lightweight Blood on the Clocktower-style game using a custom script.

## Features

- Create and manage a single game per guild.
- Players join/leave lobby.
- Storyteller can add AI bot players to fill seats.
- Start game with automatic role distribution based on player count.
- DM role cards to players.
- Keep role assignments hidden from public chat.
- Simple day/night tracking.
- Mark players dead by execution or at night.
- Run simple AI-driven day/night actions.
- Show alive/dead lists.
- Lookup role descriptions.

## Install

From your Red bot:

```text
[p]repo add ben-cogs https://github.com/BenCos17/ben-cogs
[p]cog install ben-cogs bloodontheclocktower
[p]load bloodontheclocktower
```

## Commands

Use the command group: `[p]botc`

- `[p]botc create` - create a new lobby in the current channel.
- `[p]botc join` - join the current lobby.
- `[p]botc leave` - leave before the game starts.
- `[p]botc players` - show players and alive/dead state.
- `[p]botc addbots <count>` - add AI bot players in lobby (storyteller only).
- `[p]botc clearbots` - remove all AI bot players before start (storyteller only).
- `[p]botc start` - assign roles and start night 1.
- `[p]botc day` / `[p]botc night` - switch phase.
- `[p]botc execute <target>` - open an execution vote for a target (day only, storyteller only).
- `[p]botc vote <yes|no>` - cast your vote on the active execution vote (alive players).
- `[p]botc tally` - close the vote and resolve execution result (storyteller only).
- `[p]botc kill <target>` - mark a player dead at night (mention, ID, or exact name like `Bot 1`).
- `[p]botc aisteps [count]` - run AI actions for current phase (storyteller only).
- `[p]botc info <role name>` - show role text.
- `[p]botc reveal` - storyteller-only assignment dump to DM.
- `[p]botc debugrole <target>` - storyteller debug role peek to DM. If storyteller is also a player, posts a public cheat notice in the game channel.
- `[p]botc end` - end and clear the game.

## Notes

This is a moderator/storyteller-assist implementation, not a full automation of every character interaction.
AI actions are intentionally simple and random to support low-player or bot-heavy games.
Day AI actions now simulate votes before execution instead of always executing.
The storyteller can still be a player, but using debug role peeks while playing is publicly announced.

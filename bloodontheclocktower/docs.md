# bloodontheclocktower

A Red-DiscordBot cog for running a lightweight Blood on the Clocktower-style game using a custom script.

## Features

- Create and manage a single game per guild.
- Players join/leave lobby.
- Start game with automatic role distribution based on player count.
- DM role cards to players.
- Simple day/night tracking.
- Mark players dead by execution or at night.
- Show alive/dead lists.
- Lookup role descriptions.

## Install

From your Red bot:

```text
[p]repo add ben-cogs <your-repo-url>
[p]cog install ben-cogs bloodontheclocktower
[p]load bloodontheclocktower
```

## Commands

Use the command group: `[p]botc`

- `[p]botc create` - create a new lobby in the current channel.
- `[p]botc join` - join the current lobby.
- `[p]botc leave` - leave before the game starts.
- `[p]botc players` - show players and alive/dead state.
- `[p]botc start` - assign roles and start night 1.
- `[p]botc day` / `[p]botc night` - switch phase.
- `[p]botc execute @user` - mark a player dead by execution.
- `[p]botc kill @user` - mark a player dead at night.
- `[p]botc info <role name>` - show role text.
- `[p]botc reveal` - storyteller-only assignment dump.
- `[p]botc end` - end and clear the game.

## Notes

This is a moderator/storyteller-assist implementation, not a full automation of every character interaction.

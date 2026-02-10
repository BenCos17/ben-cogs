# Tips Cog

A small Red cog that posts random tips and provides an interactive button-based settings menu for the bot owner.

**Overview**

- Posts a random tip with the `tip` command.
- Owner-only commands let you add/remove tips and open a button-based settings UI.
- Settings (cooldown, color, title, tips list) are persisted to Red `Config` (global scope), so they survive restarts.

**Commands**

- `tip`
  - Usage: `[prefix]tip`
  - Posts a random tip embed. Each user has a per-user cooldown (default 60s).

- `addtip <tip>` (owner-only)
  - Usage: `[prefix]addtip This is a new tip.`
  - Adds a tip to the saved tips list and persists it.

- `removetip <index>` (owner-only)
  - Usage: `[prefix]removetip 2`
  - Removes the tip at the given zero-based index from the saved list.

 `tipset` (owner-only)
  - Usage: `[prefix]tipset`
  - Opens an interactive embed with buttons for configuring cooldown, color, title, and closing the menu.
**Button UI behaviour**

- Only the user who invoked `tipconfig` may interact with the buttons.
- Buttons and flows:
  - `Cooldown` (Primary): Bot asks (ephemeral) "Please type the new cooldown in seconds." Type a number in the same channel within 60 seconds. The value is validated and saved to config.
  - `Color` (Secondary): Bot asks (ephemeral) "Please type a color name (blue, red, green)." Type one of the supported names within 60 seconds. The chosen color name is saved to config (the embed color updates).
  - `Title` (Success): Bot asks (ephemeral) "Please type the new title for tips." Type the title within 120 seconds; it is saved to config and the embed updates.
  - `Close` (Danger): Deletes the settings message.
- Timeouts: the view will time out after 120 seconds; individual prompts have the timeouts described above.

**Config (global)**

The cog uses Red `Config` with the following global keys (registered with defaults):

- `cooldown` (int)
  - Default: `60`
  - Per-user cooldown in seconds between `tip` requests.

- `tip_color` (str)
  - Default: `"blue"`
  - Stored as a string; the cog maps it to a `discord.Color` (supported names: `blue`, `red`, `green`).

- `tip_title` (str)
  - Default: `"💡 Random Tip"`
  - The embed title used when posting tips.

- `tips` (list[str])
  - Default: initial example tips included with the cog.
  - The full list of tips the cog will choose from.

Notes:
- All changes made via commands or the button UI are persisted immediately using `Config.set`.
- If you need additional color options, edit the cog to add more mappings in the color map.

**Examples**

- Add a tip (owner):
  - `[p]addtip Remember to check pinned messages.`

- Remove tip index 0 (owner):
  - `[p]removetip 0`

- Open the settings UI (owner):
  - `[p]tipconfig`
  - Click `Cooldown`, type `30` in the channel when prompted (ephemeral prompts are used for the request itself).

**Troubleshooting**

- Buttons don't respond:
  - Confirm you are the user who ran `[p]tipconfig`.
  - The view times out after 120s; re-run `[p]tipconfig` to re-open.

- Config changes didn't persist:
  - Confirm the bot has permission to write to its data store (Red handles this normally).
  - Check that the cog is loaded and that no exceptions appear in the bot logs.

**Extending**

- Add more color names by updating the `color_map` in `tips/tips.py` and adding the corresponding `discord.Color` entries.
- Change permissions (for example allow server admins to use `tipconfig`) by replacing the owner-only check on the command with an appropriate Red permission decorator.

---

File: `tips/tips.py` — this document documents the behavior of the interactive settings UI and the persistence keys used in Red `Config`.

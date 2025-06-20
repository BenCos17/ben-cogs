# DnD Cog Documentation

This cog provides a set of commands for a Discord bot to facilitate a Dungeons & Dragons (DnD) experience. It includes features for character creation, dice rolling, initiative tracking, inventory, and session note management.

## Commands

### `dndgame`

* **Description:** A fun, standalone DnD adventure simulation with dice rolling and narrative.
* **Cooldown:** 1 minute per user.
* **Usage:** `!dndgame`
* **Functionality:** A mini-game where you choose a class and fight monsters.

---

### `dndtools` (Command Group)

* **Description:** Main command group for DnD session tools. Aliases: `dndt`, `dtools`
* **Usage:** `!dndtools <subcommand> [args]`
* **Subcommands:**

#### `roll` / `dice`
* **Description:** Roll dice using standard notation, e.g., 2d6+3.
* **Usage:** `!dndtools roll <dice notation>`
* **Functionality:** Parses the dice notation, rolls the dice, and displays the result.

#### `advantage`
* **Description:** Roll with advantage (2d20, take highest).
* **Usage:** `!dndtools advantage`
* **Functionality:** Rolls two d20s and returns the highest result.

#### `disadvantage`
* **Description:** Roll with disadvantage (2d20, take lowest).
* **Usage:** `!dndtools disadvantage`
* **Functionality:** Rolls two d20s and returns the lowest result.

#### `stats`
* **Description:** Roll 4d6 and drop the lowest die, repeated 6 times for character stats.
* **Usage:** `!dndtools stats`
* **Functionality:** Generates a standard set of 6 ability scores for a new character.

#### `rollset`
* **Description:** Roll multiple sets of dice.
* **Usage:** `!dndtools rollset <dice> <count>`
* **Functionality:** Rolls a specified dice notation a given number of times.

#### `createchar`
* **Description:** Create your DnD character.
* **Usage:** `!dndtools createchar <name> <class> <hp> <str> <dex> <con> <int> <wis> <cha>`
* **Functionality:** Creates a character with the specified attributes and stores it in the user's configuration.

#### `viewchar`
* **Description:** View your DnD character sheet.
* **Usage:** `!dndtools viewchar`
* **Functionality:** Retrieves the user's character from their configuration and displays it in an embed.

#### `initiative`
* **Description:** Start initiative order.
* **Usage:** `!dndtools initiative @player1 @player2 ...`
* **Functionality:** Sets the initiative order for the specified players and starts the first turn.

#### `nextturn`
* **Description:** Advance to the next turn in initiative order.
* **Usage:** `!dndtools nextturn`
* **Functionality:** Advances the initiative order to the next player's turn and announces whose turn it is.

#### `clearinitiative`
* **Description:** Clear the initiative order for this server.
* **Usage:** `!dndtools clearinitiative`
* **Functionality:** Removes all players from the initiative order and resets the turn counter.

#### `addnpc`
* **Description:** Add a custom NPC to the campaign.
* **Usage:** `!dndtools addnpc <name> <description>`
* **Functionality:** Stores a custom NPC with a name and description for the current server.

#### `viewnpc`
* **Description:** View all custom NPCs for the campaign.
* **Usage:** `!dndtools viewnpc`
* **Functionality:** Displays a list of all custom NPCs saved for the server.

#### `additem`
* **Description:** Add an item to your inventory.
* **Usage:** `!dndtools additem <item>`
* **Functionality:** Adds the specified item to the user's inventory.

#### `viewitems`
* **Description:** View your inventory.
* **Usage:** `!dndtools viewitems`
* **Functionality:** Displays the user's current inventory.

#### `clearitems`
* **Description:** Clear your inventory.
* **Usage:** `!dndtools clearitems`
* **Functionality:** Removes all items from the user's inventory.

#### `addnote`
* **Description:** Add a session note.
* **Usage:** `!dndtools addnote <note>`
* **Functionality:** Adds the specified note to the session notes for the guild.

#### `viewnotes`
* **Description:** View all session notes.
* **Usage:** `!dndtools viewnotes`
* **Functionality:** Displays all session notes for the guild.

#### `clearnotes`
* **Description:** Clear all session notes for this server.
* **Usage:** `!dndtools clearnotes`
* **Functionality:** Removes all session notes for the guild.

---

**Note:** All `dndtools` subcommands can be accessed using the aliases `dndt` or `dtools` as the command group name.

Example: `!dndt roll 1d20+5` or `!dtools additem Healing Potion`

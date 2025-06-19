# DnD Cog Documentation

This cog provides a set of commands for a Discord bot to facilitate a Dungeons & Dragons (DnD) experience. It includes features for character creation, dice rolling, initiative tracking, and session note management.

## Commands

### `dndtools`

* **Description:** A complex DnD command with dice rolling.
* **Cooldown:** 1 minute per user.
* **Usage:** `!dndtools`
* **Functionality:** Rolls a D20, displays player and enemy stats, simulates combat, and provides a narrative for the adventure.

### `dndroll`

* **Description:** Roll dice using standard notation, e.g., 2d6+3.
* **Usage:** `!dndroll <dice notation>`
* **Functionality:** Parses the dice notation, rolls the dice, and displays the result.

### `createchar`

* **Description:** Create your DnD character.
* **Usage:** `!createchar <name> <class> <hp> <str> <dex> <con> <int> <wis> <cha>`
* **Functionality:** Creates a character with the specified attributes and stores it in the user's configuration.

### `viewchar`

* **Description:** View your DnD character sheet.
* **Usage:** `!viewchar`
* **Functionality:** Retrieves the user's character from their configuration and displays it in an embed.

### `initiative`

* **Description:** Start initiative order.
* **Usage:** `!initiative @player1 @player2 ...`
* **Functionality:** Sets the initiative order for the specified players and starts the first turn.

### `nextturn`

* **Description:** Advance to the next turn in initiative order.
* **Usage:** `!nextturn`
* **Functionality:** Advances the initiative order to the next player's turn and announces whose turn it is.

### `additem`

* **Description:** Add an item to your inventory.
* **Usage:** `!additem <item>`
* **Functionality:** Adds the specified item to the user's inventory.

### `viewitems`

* **Description:** View your inventory.
* **Usage:** `!viewitems`
* **Functionality:** Displays the user's current inventory.

### `addnote`

* **Description:** Add a session note.
* **Usage:** `!addnote <note>`
* **Functionality:** Adds the specified note to the session notes for the guild.

### `viewnotes`

* **Description:** View all session notes.
* **Usage:** `!viewnotes`
* **Functionality:** Displays all session notes for the guild.

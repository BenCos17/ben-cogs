import random
from redbot.core import commands, Config
import re
import asyncio
from typing import Dict, List, Optional
import discord


class Character:
    def __init__(self, name: str, char_class: str, level: int = 1):
        self.name = name
        self.char_class = char_class
        self.level = level
        self.xp = 0
        
        # Base stats by class
        class_stats = {
            "warrior": {"hp": 20, "attack": 15, "defense": 12, "abilities": ["Shield Block", "Heavy Strike"]},
            "mage": {"hp": 12, "attack": 18, "defense": 8, "abilities": ["Fireball", "Magic Shield"]},
            "rogue": {"hp": 15, "attack": 16, "defense": 10, "abilities": ["Backstab", "Dodge"]},
            "cleric": {"hp": 16, "attack": 14, "defense": 11, "abilities": ["Heal", "Smite"]}
        }
        
        stats = class_stats.get(char_class.lower(), class_stats["warrior"])
        self.max_hp = stats["hp"] + (level - 1) * 5
        self.hp = self.max_hp
        self.attack = stats["attack"] + (level - 1) * 2
        self.defense = stats["defense"] + (level - 1)
        self.abilities = stats["abilities"]
        self.inventory = []

    def use_ability(self, ability_name: str) -> tuple[str, int]:
        ability_effects = {
            "Shield Block": ("increases defense for one turn", 5),
            "Heavy Strike": ("deals heavy damage", 20),
            "Fireball": ("deals area damage", 25),
            "Magic Shield": ("creates a magical barrier", 8),
            "Backstab": ("deals critical damage", 30),
            "Dodge": ("increases evasion for one turn", 7),
            "Heal": ("restores health", 15),
            "Smite": ("deals holy damage", 22)
        }
        return ability_effects.get(ability_name, ("does nothing", 0))

class Enemy:
    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level
        
        # Expanded enemy types with base stats
        enemy_types = {
            "Goblin": {"hp": 12, "attack": 8, "defense": 5, "xp": 50, "loot_chance": 0.3},
            "Orc": {"hp": 20, "attack": 12, "defense": 8, "xp": 100, "loot_chance": 0.4},
            "Dragon": {"hp": 50, "attack": 20, "defense": 15, "xp": 500, "loot_chance": 0.8},
            "Skeleton": {"hp": 15, "attack": 10, "defense": 6, "xp": 75, "loot_chance": 0.3},
            "Troll": {"hp": 30, "attack": 15, "defense": 10, "xp": 200, "loot_chance": 0.5},
            "Bandit": {"hp": 18, "attack": 11, "defense": 7, "xp": 80, "loot_chance": 0.6},
            "Wolf": {"hp": 14, "attack": 12, "defense": 5, "xp": 60, "loot_chance": 0.2},
            "Giant Spider": {"hp": 16, "attack": 13, "defense": 6, "xp": 90, "loot_chance": 0.3},
            "Undead Knight": {"hp": 25, "attack": 14, "defense": 12, "xp": 150, "loot_chance": 0.5},
            "Dark Mage": {"hp": 22, "attack": 16, "defense": 7, "xp": 180, "loot_chance": 0.7},
            "Demon": {"hp": 35, "attack": 18, "defense": 13, "xp": 300, "loot_chance": 0.6},
            "Ancient Dragon": {"hp": 60, "attack": 25, "defense": 18, "xp": 800, "loot_chance": 1.0}
        }
        
        stats = enemy_types.get(name, enemy_types["Goblin"])
        self.max_hp = stats["hp"] + (level - 1) * 3
        self.hp = self.max_hp
        self.attack = stats["attack"] + (level - 1) * 2
        self.defense = stats["defense"] + (level - 1)
        self.xp = stats["xp"] * level
        self.loot_chance = stats["loot_chance"]

    def _generate_loot(self, enemy_level: int) -> str:
        loot_table = [
            "Health Potion",
            "Mana Potion",
            "Scroll of Fireball",
            "Scroll of Lightning",
            "Healing Salve",
            "Magic Shield Scroll",
            "Ring of Protection",
            "Amulet of Power",
            "Elixir of Strength",
            "Boots of Speed",
            "Cloak of Stealth",
            "Bracers of Defense",
            "Wand of Magic Missiles",
            "Staff of Healing",
            "Sword of Sharpness",
            "Armor of Resistance"
        ]
        
        rare_loot = [
            "Dragon Scale Armor",
            "Flaming Sword",
            "Staff of Power",
            "Ring of Invisibility",
            "Amulet of Life",
            "Boots of Flying",
            "Cloak of Displacement",
            "Gauntlets of Ogre Power"
        ]
        
        if enemy_level >= 5 and random.random() < 0.2:  # 20% chance for rare loot at higher levels
            return random.choice(rare_loot)
        return random.choice(loot_table)

class DnD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_user(
            character=None,  # dict or None
            inventory=[],
            active_effects=[]  # for tracking ongoing effects in campaigns
        )
        self.config.register_guild(
            initiative_order=[],  # list of user_ids
            current_turn=0,
            session_notes=[],  # list of (author, note)
            campaign_state={},  # for tracking campaign progress
            custom_npcs=[]  # for storing custom NPCs
        )

    @commands.command(name='dndgame', help='Start a DnD adventure game!')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def dndgame(self, ctx):
        # Character creation
        await ctx.send("Welcome to the adventure! Choose your class:\n1. Warrior\n2. Mage\n3. Rogue\n4. Cleric")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            class_choice = msg.content.lower()
            
            class_map = {
                "1": "warrior", "warrior": "warrior",
                "2": "mage", "mage": "mage",
                "3": "rogue", "rogue": "rogue",
                "4": "cleric", "cleric": "cleric"
            }
            
            if class_choice not in class_map and class_choice not in class_map.values():
                await ctx.send("Invalid class choice. Defaulting to Warrior.")
                class_choice = "warrior"
            else:
                class_choice = class_map.get(class_choice, class_choice)
            
            player = Character(ctx.author.display_name, class_choice)
            await ctx.send(f"A new {class_choice.title()} begins their journey!")
            
            # Game loop
            await self._adventure_loop(ctx, player)
            
        except asyncio.TimeoutError:
            await ctx.send("Character creation timed out.")
            return

    async def _adventure_loop(self, ctx, player: Character):
        locations = ["Forest", "Dungeon", "Cave", "Castle", "Ruins"]
        current_location = random.choice(locations)
        
        embed = discord.Embed(title="Adventure Begins!", description=f"You find yourself in a mysterious {current_location}.", color=discord.Color.green())
        embed.add_field(name="Your Stats", value=f"HP: {player.hp}/{player.max_hp}\nAttack: {player.attack}\nDefense: {player.defense}", inline=False)
        embed.add_field(name="Abilities", value="\n".join(player.abilities), inline=False)
        await ctx.send(embed=embed)
        
        # Adventure phases
        while player.hp > 0:
            # Random encounter
            if random.random() < 0.7:  # 70% chance of combat
                enemy_types = ["Goblin", "Orc", "Skeleton", "Troll"]
                if player.level >= 5:
                    enemy_types.append("Dragon")
                
                enemy = Enemy(random.choice(enemy_types), max(1, player.level - 1))
                await self._combat_loop(ctx, player, enemy)
                
                if player.hp <= 0:
                    await ctx.send("Game Over! Your adventure ends here...")
                    break
                
                # Reward
                xp_gain = enemy.level * 50
                player.xp += xp_gain
                await ctx.send(f"You gained {xp_gain} XP!")
                
                # Level up check
                if player.xp >= player.level * 100:
                    player.level += 1
                    player.max_hp += 5
                    player.hp = player.max_hp
                    player.attack += 2
                    player.defense += 1
                    await ctx.send(f"Level Up! You are now level {player.level}!")
                
                # Loot
                if random.random() < 0.4:  # 40% chance of loot
                    loot = self._generate_loot(enemy.level)
                    player.inventory.append(loot)
                    await ctx.send(f"You found: {loot}!")
            
            else:  # Rest spot
                await ctx.send("You find a safe spot to rest...")
                healing = min(player.max_hp - player.hp, player.max_hp // 2)
                player.hp += healing
                await ctx.send(f"You recovered {healing} HP! Current HP: {player.hp}/{player.max_hp}")
            
            # Continue adventure?
            await ctx.send("Continue the adventure? (yes/no)")
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                if msg.content.lower() not in ['yes', 'y', 'continue']:
                    await ctx.send("You decide to end your adventure here.")
                    break
            except asyncio.TimeoutError:
                await ctx.send("No response received. Ending adventure.")
                break
            
            # Change location
            current_location = random.choice([loc for loc in locations if loc != current_location])
            await ctx.send(f"You travel to a new location: {current_location}")

    async def _combat_loop(self, ctx, player: Character, enemy: Enemy):
        embed = discord.Embed(title="Combat Begins!", description=f"A {enemy.name} appears!", color=discord.Color.red())
        embed.add_field(name="Enemy Stats", value=f"HP: {enemy.hp}/{enemy.max_hp}\nAttack: {enemy.attack}\nDefense: {enemy.defense}", inline=False)
        await ctx.send(embed=embed)
        
        # Initiative roll
        player_init = random.randint(1, 20)
        enemy_init = random.randint(1, 20)
        player_first = player_init >= enemy_init
        
        while player.hp > 0 and enemy.hp > 0:
            if player_first:
                # Player turn
                await self._player_turn(ctx, player, enemy)
                if enemy.hp <= 0:
                    await ctx.send(f"You defeated the {enemy.name}!")
                    break
                
                # Enemy turn
                await self._enemy_turn(ctx, player, enemy)
                if player.hp <= 0:
                    await ctx.send("You have been defeated!")
                    break
            else:
                # Enemy turn
                await self._enemy_turn(ctx, player, enemy)
                if player.hp <= 0:
                    await ctx.send("You have been defeated!")
                    break
                
                # Player turn
                await self._player_turn(ctx, player, enemy)
                if enemy.hp <= 0:
                    await ctx.send(f"You defeated the {enemy.name}!")
                    break

    async def _player_turn(self, ctx, player: Character, enemy: Enemy):
        # Show combat options
        options = ["1. Attack", "2. Use Ability", "3. Check Stats", "4. Use Item"]
        await ctx.send("Your turn! Choose your action:\n" + "\n".join(options))
        
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            choice = msg.content.lower()
            
            if choice in ['1', 'attack']:
                damage = max(0, player.attack - enemy.defense)
                enemy.hp -= damage
                await ctx.send(f"You deal {damage} damage to the {enemy.name}!")
            
            elif choice in ['2', 'ability']:
                if not player.abilities:
                    await ctx.send("You have no abilities available!")
                    return
                
                await ctx.send("Choose an ability:\n" + "\n".join(f"{i+1}. {ability}" for i, ability in enumerate(player.abilities)))
                try:
                    msg = await self.bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                    ability_idx = int(msg.content) - 1
                    if 0 <= ability_idx < len(player.abilities):
                        ability = player.abilities[ability_idx]
                        effect, value = player.use_ability(ability)
                        if "damage" in effect:
                            enemy.hp -= value
                            await ctx.send(f"You use {ability} and deal {value} damage!")
                        elif "defense" in effect or "barrier" in effect:
                            player.defense += value
                            await ctx.send(f"You use {ability} and gain {value} defense!")
                        elif "health" in effect:
                            healing = min(value, player.max_hp - player.hp)
                            player.hp += healing
                            await ctx.send(f"You use {ability} and heal for {healing} HP!")
                except (ValueError, IndexError):
                    await ctx.send("Invalid ability choice. Turn skipped.")
            
            elif choice in ['3', 'stats']:
                embed = discord.Embed(title="Combat Stats", color=discord.Color.blue())
                embed.add_field(name="Your Stats", value=f"HP: {player.hp}/{player.max_hp}\nAttack: {player.attack}\nDefense: {player.defense}", inline=True)
                embed.add_field(name="Enemy Stats", value=f"HP: {enemy.hp}/{enemy.max_hp}\nAttack: {enemy.attack}\nDefense: {enemy.defense}", inline=True)
                await ctx.send(embed=embed)
                await self._player_turn(ctx, player, enemy)  # Let player choose another action
            
            elif choice in ['4', 'item']:
                if not player.inventory:
                    await ctx.send("You have no items!")
                    return
                
                await ctx.send("Choose an item to use:\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(player.inventory)))
                try:
                    msg = await self.bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                    item_idx = int(msg.content) - 1
                    if 0 <= item_idx < len(player.inventory):
                        item = player.inventory.pop(item_idx)
                        if "Potion" in item:
                            healing = 20
                            player.hp = min(player.max_hp, player.hp + healing)
                            await ctx.send(f"You use {item} and heal for {healing} HP!")
                        elif "Scroll" in item:
                            enemy.hp -= 25
                            await ctx.send(f"You use {item} and deal 25 magic damage!")
                except (ValueError, IndexError):
                    await ctx.send("Invalid item choice. Turn skipped.")
            
        except asyncio.TimeoutError:
            await ctx.send("Turn skipped due to timeout.")

    async def _enemy_turn(self, ctx, player: Character, enemy: Enemy):
        damage = max(0, enemy.attack - player.defense)
        player.hp -= damage
        await ctx.send(f"The {enemy.name} attacks you for {damage} damage!")

    def _generate_loot(self, enemy_level: int) -> str:
        loot_table = [
            "Health Potion",
            "Mana Potion",
            "Scroll of Fireball",
            "Scroll of Lightning",
            "Healing Salve",
            "Magic Shield Scroll",
            "Ring of Protection",
            "Amulet of Power",
            "Elixir of Strength",
            "Boots of Speed",
            "Cloak of Stealth",
            "Bracers of Defense",
            "Wand of Magic Missiles",
            "Staff of Healing",
            "Sword of Sharpness",
            "Armor of Resistance"
        ]
        
        rare_loot = [
            "Dragon Scale Armor",
            "Flaming Sword",
            "Staff of Power",
            "Ring of Invisibility",
            "Amulet of Life",
            "Boots of Flying",
            "Cloak of Displacement",
            "Gauntlets of Ogre Power"
        ]
        
        if enemy_level >= 5 and random.random() < 0.2:  # 20% chance for rare loot at higher levels
            return random.choice(rare_loot)
        return random.choice(loot_table)

    @commands.group(name='dndtools', invoke_without_command=True, aliases=["dndt", "dtools"], help='DnD Dungeon Master tools for running campaigns')
    async def dndtools(self, ctx):
        if ctx.invoked_subcommand is None:
            commands_list = [
                "**Dice Commands:**",
                "`roll <dice>` - Roll any dice (e.g., d20, 2d6+3)",
                "`advantage` - Roll with advantage (2d20, take highest)",
                "`disadvantage` - Roll with disadvantage (2d20, take lowest)",
                "`stats` - Roll 4d6 drop lowest for character stats",
                "`rollset <dice> <count>` - Roll multiple sets (e.g., rollset 2d6 4)",
                "\n**Campaign Tools:**",
                "`createchar` - Create character sheet",
                "`viewchar` - View character sheet",
                "`initiative` - Manage combat initiative",
                "`addnpc` - Add custom NPC",
                "`viewnpc` - View custom NPCs",
                "`additem/viewitems` - Manage inventory",
                "`addnote/viewnotes` - Session notes"
            ]
            await ctx.send("\n".join(commands_list))

    @dndtools.command(name='advantage', help='Roll with advantage (2d20, take highest)')
    async def advantage(self, ctx):
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        result = max(roll1, roll2)
        await ctx.send(f"Rolling with advantage: [{roll1}, {roll2}] = **{result}**")

    @dndtools.command(name='disadvantage', help='Roll with disadvantage (2d20, take lowest)')
    async def disadvantage(self, ctx):
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        result = min(roll1, roll2)
        await ctx.send(f"Rolling with disadvantage: [{roll1}, {roll2}] = **{result}**")

    @dndtools.command(name='stats', help='Roll 4d6 drop lowest for character stats')
    async def rollstats(self, ctx):
        stats = []
        rolls_detail = []
        for _ in range(6):
            rolls = sorted([random.randint(1, 6) for _ in range(4)])
            total = sum(rolls[1:])  # Drop lowest
            stats.append(total)
            rolls_detail.append(f"{rolls} → {total}")
        
        embed = discord.Embed(title="Character Stat Rolls", description="4d6 drop lowest", color=discord.Color.blue())
        embed.add_field(name="Detailed Rolls", value="\n".join(rolls_detail), inline=False)
        embed.add_field(name="Final Stats", value=", ".join(map(str, stats)), inline=False)
        await ctx.send(embed=embed)

    @dndtools.command(name='rollset', help='Roll multiple sets of dice')
    async def rollset(self, ctx, dice: str, count: int = 1):
        if count > 10:
            await ctx.send("Maximum 10 sets at once.")
            return
        
        results = []
        for i in range(count):
            match = re.fullmatch(r"(\d*)d(\d+)([+-]\d+)?", dice.replace(" ", ""))
            if not match:
                await ctx.send("Invalid dice notation. Use NdM+X, e.g. 2d6+3")
                return
            
            n, die, mod = match.groups()
            n = int(n) if n else 1
            die = int(die)
            mod = int(mod) if mod else 0
            
            rolls = [random.randint(1, die) for _ in range(n)]
            total = sum(rolls) + mod
            results.append(f"Set {i+1}: {rolls} {'+'+str(mod) if mod else ''} = **{total}**")
        
        await ctx.send("\n".join(results))

    @dndtools.command(name='addnpc', help='Add a custom NPC to the campaign')
    async def addnpc(self, ctx, name: str, *, description: str):
        npcs = await self.config.guild(ctx.guild).custom_npcs()
        npcs.append({"name": name, "description": description})
        await self.config.guild(ctx.guild).custom_npcs.set(npcs)
        await ctx.send(f"NPC {name} added to the campaign.")

    @dndtools.command(name='viewnpc', help='View all custom NPCs')
    async def viewnpc(self, ctx):
        npcs = await self.config.guild(ctx.guild).custom_npcs()
        if not npcs:
            await ctx.send("No custom NPCs found.")
            return
        
        embed = discord.Embed(title="Campaign NPCs", color=discord.Color.green())
        for npc in npcs:
            embed.add_field(name=npc["name"], value=npc["description"], inline=False)
        await ctx.send(embed=embed)

    @dndtools.command(name='createchar', help='Create your DnD character: dndtools createchar <name> <class> <hp> <str> <dex> <con> <int> <wis> <cha>')
    async def createchar(self, ctx, name: str, char_class: str, hp: int, str_: int, dex: int, con: int, int_: int, wis: int, cha: int):
        char = {
            'name': name,
            'class': char_class,
            'hp': hp,
            'str': str_,
            'dex': dex,
            'con': con,
            'int': int_,
            'wis': wis,
            'cha': cha
        }
        await self.config.user(ctx.author).character.set(char)
        await ctx.send(f"Character created for {ctx.author.display_name}: {name} the {char_class} (HP: {hp})")

    @dndtools.command(name='viewchar', help='View your DnD character sheet')
    async def viewchar(self, ctx):
        char = await self.config.user(ctx.author).character()
        if not char:
            await ctx.send("No character found. Use dndtools createchar to make one.")
            return
        embed = self._char_embed(char, ctx.author.display_name)
        await ctx.send(embed=embed)

    def _char_embed(self, char, owner):
        embed = discord.Embed(title=f"{char['name']} the {char['class']}", description=f"Owner: {owner}", color=discord.Color.purple())
        embed.add_field(name="HP", value=char['hp'])
        embed.add_field(name="STR", value=char['str'])
        embed.add_field(name="DEX", value=char['dex'])
        embed.add_field(name="CON", value=char['con'])
        embed.add_field(name="INT", value=char['int'])
        embed.add_field(name="WIS", value=char['wis'])
        embed.add_field(name="CHA", value=char['cha'])
        return embed

    @dndtools.command(name='initiative', help='Start initiative order: dndtools initiative @player1 @player2 ...')
    async def initiative(self, ctx, *players: commands.MemberConverter):
        if not players:
            await ctx.send("You must mention at least one player.")
            return
        user_ids = [p.id for p in players]
        await self.config.guild(ctx.guild).initiative_order.set(user_ids)
        await self.config.guild(ctx.guild).current_turn.set(0)
        names = ', '.join(p.display_name for p in players)
        await ctx.send(f"Initiative order set: {names}. {players[0].display_name} goes first!")

    @dndtools.command(name='nextturn', help='Advance to the next turn in initiative order')
    async def nextturn(self, ctx):
        order = await self.config.guild(ctx.guild).initiative_order()
        if not order:
            await ctx.send("No initiative order set. Use dndtools initiative first.")
            return
        turn = await self.config.guild(ctx.guild).current_turn()
        turn = (turn + 1) % len(order)
        await self.config.guild(ctx.guild).current_turn.set(turn)
        user_id = order[turn]
        member = ctx.guild.get_member(user_id)
        if not member:
            await ctx.send(f"User with ID {user_id} not found in this server.")
            return
        await ctx.send(f"It's now {member.display_name}'s turn!")

    @dndtools.command(name='clearinitiative', help='Clear the initiative order for this server.')
    async def clearinitiative(self, ctx):
        await self.config.guild(ctx.guild).initiative_order.set([])
        await self.config.guild(ctx.guild).current_turn.set(0)
        await ctx.send("Initiative order cleared.")

    @dndtools.command(name='additem', help='Add an item to your inventory: dndtools additem <item>')
    async def additem(self, ctx, *, item: str):
        inv = await self.config.user(ctx.author).inventory()
        inv.append(item)
        await self.config.user(ctx.author).inventory.set(inv)
        await ctx.send(f"Added '{item}' to your inventory.")

    @dndtools.command(name='viewitems', help='View your inventory')
    async def viewitems(self, ctx):
        inv = await self.config.user(ctx.author).inventory()
        if not inv:
            await ctx.send("Your inventory is empty.")
            return
        await ctx.send(f"Your inventory: {', '.join(inv)}")

    @dndtools.command(name='clearitems', help='Clear your inventory.')
    async def clearitems(self, ctx):
        await self.config.user(ctx.author).inventory.set([])
        await ctx.send("Your inventory has been cleared.")

    @dndtools.command(name='addnote', help='Add a session note: dndtools addnote <note>')
    async def addnote(self, ctx, *, note: str):
        notes = await self.config.guild(ctx.guild).session_notes()
        notes.append((ctx.author.display_name, note))
        await self.config.guild(ctx.guild).session_notes.set(notes)
        await ctx.send("Note added.")

    @dndtools.command(name='viewnotes', help='View all session notes')
    async def viewnotes(self, ctx):
        notes = await self.config.guild(ctx.guild).session_notes()
        if not notes:
            await ctx.send("No session notes yet.")
            return
        notes_str = '\n'.join([f"{author}: {note}" for author, note in notes])
        await ctx.send(f"Session Notes:\n{notes_str}")

    @dndtools.command(name='clearnotes', help='Clear all session notes for this server.')
    async def clearnotes(self, ctx):
        await self.config.guild(ctx.guild).session_notes.set([])
        await ctx.send("All session notes have been cleared.")

    @dndtools.command(name='roll', aliases=["dice"], help='Roll dice using standard notation, e.g. 2d6+3')
    async def roll(self, ctx, *, dice: str):
        match = re.fullmatch(r"(\d*)d(\d+)([+-]\d+)?", dice.replace(" ", ""))
        if not match:
            await ctx.send("Invalid dice notation. Use NdM+X, e.g. 2d6+3.")
            return
        n, die, mod = match.groups()
        n = int(n) if n else 1
        die = int(die)
        mod = int(mod) if mod else 0
        if n < 1 or die < 1 or n > 100:
            await ctx.send("Invalid dice parameters. Max 100 dice, min 1.")
            return
        rolls = [random.randint(1, die) for _ in range(n)]
        total = sum(rolls) + mod
        await ctx.send(f"Rolling {dice}: {rolls} {'+'+str(mod) if mod else ''} = **{total}**")

import random
from redbot.core import commands, Config
import re


class DnD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_user(
            character=None,  # dict or None
            inventory=[]
        )
        self.config.register_guild(
            initiative_order=[],  # list of user_ids
            current_turn=0,
            session_notes=[]  # list of (author, note)
        )

    @commands.command(name='dndadventure', help='A fun DnD adventure simulation!')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def dndadventure(self, ctx):
        import discord
        embed = discord.Embed(title='DnD Command', description='A complex DnD command with dice rolling', color=discord.Color.blue())
        dice_roll = random.randint(1, 20)
        embed.add_field(name='Dice Roll', value=f'Rolling a D20... Result: {dice_roll}', inline=False)
        await ctx.send(embed=embed)

        embed_info = discord.Embed(title='Additional Information', description='This is just the beginning of a grand adventure!', color=discord.Color.green())
        await ctx.send(embed=embed_info)
        
        # todo game logic, combat system, and character creation
        player_hp = 100
        player_attack = 15
        player_defense = 10
        enemy_hp = 80
        enemy_attack = 12
        enemy_defense = 8
        player_embed = discord.Embed(title='Player Stats', description=f'HP: {player_hp}, Attack: {player_attack}, Defense: {player_defense}', color=discord.Color.gold())
        enemy_embed = discord.Embed(title='Enemy Stats', description=f'HP: {enemy_hp}, Attack: {enemy_attack}, Defense: {enemy_defense}', color=discord.Color.red())
        await ctx.send(embed=player_embed)
        await ctx.send(embed=enemy_embed)
        await ctx.send('Combat begins!')

        # Custom boss added based on player's remaining stats
        boss_hp = player_hp * 2
        boss_attack = player_attack + 5
        boss_defense = player_defense + 5
        boss_embed = discord.Embed(title='Boss Stats', description=f'HP: {boss_hp}, Attack: {boss_attack}, Defense: {boss_defense}', color=discord.Color.dark_red())
        await ctx.send(embed=boss_embed)
        await ctx.send('Boss appears! Prepare for a tough battle!')

        while player_hp > 0 and (enemy_hp > 0 or boss_hp > 0):
            if enemy_hp > 0:
                player_damage = max(0, player_attack - enemy_defense)
                enemy_damage = max(0, enemy_attack - player_defense)
                player_hp -= enemy_damage
                enemy_hp -= player_damage
                await ctx.send(f'Player takes {random.randint(1, 20)} damage. Enemy takes {random.randint(1, 20)} damage.')
            else:
                player_damage = max(0, player_attack - boss_defense)
                boss_damage = max(0, boss_attack - player_defense)
                player_hp -= boss_damage
                boss_hp -= player_damage
                await ctx.send(f'Player takes {random.randint(1, 20)} damage. Boss takes {random.randint(1, 20)} damage.')

        if player_hp <= 0:
            await ctx.send('Player has been defeated!')
        elif enemy_hp <= 0 and boss_hp <= 0:
            await ctx.send('All enemies have been defeated! Victory!')
        else:
            await ctx.send('Boss has been defeated! Victory!')

        # todo better stuff and also improve the code
        await ctx.send('The dungeon reveals its secrets...')
        await ctx.send('You encounter a mysterious wizard who offers to teach you powerful spells.')
        await ctx.send('Using machine learning algorithms, you learn new spells and enhance your abilities.')
        await ctx.send('Your character evolves with the true essence of magic, unlocking unlimited potential.')
        await ctx.send('The world trembles at your newfound power as you rewrite the rules of reality.')

        # Custom items added for later use once I get round to it
        await ctx.send('You discover a hidden chest containing magical artifacts.')
        await ctx.send('These items will prove invaluable in your future adventures.')
        await ctx.send('Remember to use them wisely to overcome the greatest challenges.')

    @commands.group(name='dndtools', invoke_without_command=True, aliases=["dndt", "dtools"], help='DnD session tools: character sheets, dice, initiative, inventory, and more.')
    async def dndtools(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use a subcommand: roll, createchar, viewchar, initiative, nextturn, clearinitiative, additem, viewitems, clearitems, addnote, viewnotes, clearnotes.")

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
        import discord
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

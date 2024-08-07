# Start of Selection
import random
from redbot.core import commands


class DnD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dnd', help='A complex DnD command with dice rolling')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def dnd(self, ctx):
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

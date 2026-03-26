import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import discord
from redbot.core import commands


ROLE_INFO: Dict[str, str] = {
    "Chef": "You start knowing how many pairs of evil players there are.",
    "Investigator": "You start knowing that 1 of 2 players is a particular Minion.",
    "Washerwoman": "You start knowing that 1 of 2 players is a particular Townsfolk.",
    "Librarian": "You start knowing that 1 of 2 players is a particular Outsider (or that zero are in play).",
    "Empath": "Each night, learn how many of your 2 alive neighbors are evil.",
    "Fortune Teller": "Each night, choose 2 players; you learn if either is a Demon.",
    "Undertaker": "Each night, learn which character died by execution today.",
    "Monk": "Each night, choose a player (not yourself); they are safe from the Demon tonight.",
    "Gossip": "Each day, you may make a public statement. Tonight, if true, a player dies.",
    "Slayer": "Once per game, during the day, publicly choose a player; if they are the Demon, they die.",
    "Soldier": "You are safe from the Demon.",
    "Cannibal": "You have the ability of the recently killed executee. If they are evil, you are poisoned until a good player dies by execution.",
    "Ravenkeeper": "If you die at night, choose a player; you learn their character.",
    "Mayor": "If only 3 players live and no execution occurs, your team wins. If you die at night, another player might die instead.",
    "Fool": "The first time you die, you do not.",
    "Virgin": "The first time you are nominated, if the nominator is a Townsfolk, they are executed immediately.",
    "Butler": "Each night, choose a player (not yourself); tomorrow, you may only vote if they are voting too.",
    "Lunatic": "You think you are a Demon, but you are not. The Demon knows who you are.",
    "Drunk": "You do not know you are the Drunk. You think you are a Townsfolk character, but you are not.",
    "Recluse": "You might register as evil and as a Minion or Demon, even if dead.",
    "Klutz": "When you learn that you died, publicly choose 1 alive player; if they are evil, your team loses.",
    "Saint": "If you die by execution, your team loses.",
    "Mutant": "If you are mad about being an Outsider, you might be executed.",
    "Mezepheles": "You start knowing a secret word. The first good player to say this word becomes evil that night.",
    "Poisoner": "Each night, choose a player; they are poisoned tonight and tomorrow day.",
    "Spy": "Each night, you see the Grimoire. You might register as good and as a Townsfolk or Outsider, even if dead.",
    "Marionette": "You think you are a good character, but you are not. The Demon knows who you are. You neighbor the Demon.",
    "Wraith": "You may choose to open your eyes at night. You wake when other evil players do.",
    "Scarlet Woman": "If there are 5 or more players alive and the Demon dies, you become the Demon.",
    "Baron": "There are extra Outsiders in play. [+2 Outsiders]",
    "Yaggababble": "You start knowing a secret phrase. For each time you said it publicly today, a player might die.",
    "Imp": "Each night, choose a player; they die. If you kill yourself this way, a Minion becomes the Imp.",
    "Vortox": "Each night, choose a player; they die. Townsfolk abilities yield false info. Each day, if no one is executed, evil wins.",
    "Fang Gu": "Each night, choose a player; they die. The first Outsider this kills becomes an evil Fang Gu and you die instead. [+1 Outsider]",
}

TOWNSFOLK = [
    "Chef",
    "Investigator",
    "Washerwoman",
    "Librarian",
    "Empath",
    "Fortune Teller",
    "Undertaker",
    "Monk",
    "Gossip",
    "Slayer",
    "Soldier",
    "Cannibal",
    "Ravenkeeper",
    "Mayor",
    "Fool",
    "Virgin",
]

OUTSIDERS = ["Butler", "Lunatic", "Drunk", "Recluse", "Klutz", "Saint", "Mutant"]
MINIONS = ["Mezepheles", "Poisoner", "Spy", "Marionette", "Wraith", "Scarlet Woman", "Baron"]
DEMONS = ["Yaggababble", "Imp", "Vortox", "Fang Gu"]

# Player count -> (townsfolk, outsiders, minions, demons)
ROLE_DISTRIBUTION: Dict[int, Tuple[int, int, int, int]] = {
    5: (3, 0, 1, 1),
    6: (3, 1, 1, 1),
    7: (5, 0, 1, 1),
    8: (5, 1, 1, 1),
    9: (5, 2, 1, 1),
    10: (7, 0, 2, 1),
    11: (7, 1, 2, 1),
    12: (7, 2, 2, 1),
    13: (9, 0, 3, 1),
    14: (9, 1, 3, 1),
    15: (9, 2, 3, 1),
}


@dataclass
class GameState:
    storyteller_id: int
    channel_id: int
    players: List[int] = field(default_factory=list)
    started: bool = False
    alive: Set[int] = field(default_factory=set)
    roles: Dict[int, str] = field(default_factory=dict)
    phase: str = "lobby"
    day_number: int = 0


class BloodOnTheClocktower(commands.Cog):
    """Lightweight Blood on the Clocktower moderator-assist game cog."""

    def __init__(self, bot):
        self.bot = bot
        self.games: Dict[int, GameState] = {}

    def _get_game(self, guild_id: int) -> Optional[GameState]:
        return self.games.get(guild_id)

    def _is_storyteller(self, game: GameState, user_id: int) -> bool:
        return game.storyteller_id == user_id

    def _assign_roles(self, count: int) -> List[str]:
        tf, outs, mins, dems = ROLE_DISTRIBUTION[count]
        selected = []
        selected.extend(random.sample(TOWNSFOLK, tf))
        selected.extend(random.sample(OUTSIDERS, outs))
        selected.extend(random.sample(MINIONS, mins))
        selected.extend(random.sample(DEMONS, dems))
        random.shuffle(selected)
        return selected

    async def _dm_role(self, member: discord.Member, role_name: str) -> bool:
        text = ROLE_INFO.get(role_name, "No description available.")
        try:
            await member.send(f"Your role is **{role_name}**.\n{text}")
            return True
        except discord.Forbidden:
            return False

    async def _dm_storyteller(self, guild: discord.Guild, storyteller_id: int, message: str) -> bool:
        storyteller = guild.get_member(storyteller_id)
        if storyteller is None:
            return False
        try:
            await storyteller.send(message)
            return True
        except discord.Forbidden:
            return False

    @commands.group(name="botc")
    @commands.guild_only()
    async def botc(self, ctx: commands.Context):
        """Blood on the Clocktower commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @botc.command(name="create")
    async def botc_create(self, ctx: commands.Context):
        """Create a new game lobby."""
        if ctx.guild.id in self.games:
            await ctx.send("A game already exists in this server. Use `[p]botc end` first.")
            return

        self.games[ctx.guild.id] = GameState(
            storyteller_id=ctx.author.id,
            channel_id=ctx.channel.id,
            players=[ctx.author.id],
            started=False,
            phase="lobby",
        )
        await ctx.send(
            f"Lobby created by {ctx.author.mention}. Use `[p]botc join` to join. "
            "Use `[p]botc start` when ready (5-15 players)."
        )

    @botc.command(name="join")
    async def botc_join(self, ctx: commands.Context):
        """Join the current lobby."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active lobby. Use `[p]botc create` first.")
            return
        if game.started:
            await ctx.send("Game already started.")
            return
        if ctx.author.id in game.players:
            await ctx.send("You are already in the lobby.")
            return

        game.players.append(ctx.author.id)
        await ctx.send(f"{ctx.author.mention} joined the lobby. Players: {len(game.players)}")

    @botc.command(name="leave")
    async def botc_leave(self, ctx: commands.Context):
        """Leave the lobby before the game starts."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active game.")
            return
        if game.started:
            await ctx.send("You cannot leave after the game has started.")
            return
        if ctx.author.id not in game.players:
            await ctx.send("You are not in the lobby.")
            return

        game.players.remove(ctx.author.id)
        if not game.players:
            del self.games[ctx.guild.id]
            await ctx.send("Lobby is empty. Game removed.")
            return

        if game.storyteller_id == ctx.author.id:
            game.storyteller_id = game.players[0]
            await ctx.send(
                f"{ctx.author.mention} left. New storyteller is <@{game.storyteller_id}>."
            )
            return

        await ctx.send(f"{ctx.author.mention} left the lobby.")

    @botc.command(name="players")
    async def botc_players(self, ctx: commands.Context):
        """Show player list and state."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active game.")
            return

        lines: List[str] = []
        for uid in game.players:
            member = ctx.guild.get_member(uid)
            name = member.display_name if member else f"Unknown ({uid})"
            state = "alive" if (not game.started or uid in game.alive) else "dead"
            tag = " (Storyteller)" if uid == game.storyteller_id else ""
            lines.append(f"- {name}: {state}{tag}")

        await ctx.send("Players:\n" + "\n".join(lines))

    @botc.command(name="start")
    async def botc_start(self, ctx: commands.Context):
        """Start game and assign roles."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active game.")
            return
        if game.started:
            await ctx.send("Game already started.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can start the game.")
            return

        player_count = len(game.players)
        if player_count not in ROLE_DISTRIBUTION:
            await ctx.send("Player count must be between 5 and 15.")
            return

        roles = self._assign_roles(player_count)
        game.roles = {uid: roles[idx] for idx, uid in enumerate(game.players)}
        game.alive = set(game.players)
        game.started = True
        game.phase = "night"
        game.day_number = 1

        dm_failed: List[str] = []
        for uid in game.players:
            member = ctx.guild.get_member(uid)
            if not member:
                continue
            ok = await self._dm_role(member, game.roles[uid])
            if not ok:
                dm_failed.append(member.display_name)

        msg = "Game started. Night 1 begins now. Roles have been sent by DM."
        if dm_failed:
            msg += "\nCould not DM: " + ", ".join(dm_failed)
        msg += "\n`[p]botc reveal` sends assignment summary to storyteller DM only."
        await ctx.send(msg)

    @botc.command(name="day")
    async def botc_day(self, ctx: commands.Context):
        """Switch to day phase."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can change phase.")
            return

        game.phase = "day"
        await ctx.send(f"It is now **Day {game.day_number}**.")

    @botc.command(name="night")
    async def botc_night(self, ctx: commands.Context):
        """Switch to night phase and advance day counter."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can change phase.")
            return

        game.phase = "night"
        game.day_number += 1
        await ctx.send(f"It is now **Night {game.day_number}**.")

    @botc.command(name="execute")
    async def botc_execute(self, ctx: commands.Context, member: discord.Member):
        """Mark a player dead by execution."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can execute players.")
            return
        if member.id not in game.players:
            await ctx.send("That member is not in this game.")
            return
        if member.id not in game.alive:
            await ctx.send("That player is already dead.")
            return

        game.alive.remove(member.id)
        role = game.roles.get(member.id, "Unknown")
        await ctx.send(f"{member.mention} was executed and died.")
        await self._dm_storyteller(
            ctx.guild,
            game.storyteller_id,
            f"Execution result: {member.display_name} was **{role}**.",
        )

    @botc.command(name="kill")
    async def botc_kill(self, ctx: commands.Context, member: discord.Member):
        """Mark a player dead at night."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can kill players.")
            return
        if member.id not in game.players:
            await ctx.send("That member is not in this game.")
            return
        if member.id not in game.alive:
            await ctx.send("That player is already dead.")
            return

        game.alive.remove(member.id)
        await ctx.send(f"{member.mention} died in the night.")

    @botc.command(name="info")
    async def botc_info(self, ctx: commands.Context, *, role_name: str):
        """Show role description."""
        wanted = role_name.strip().lower()
        matched = None
        for role in ROLE_INFO:
            if role.lower() == wanted:
                matched = role
                break

        if not matched:
            await ctx.send("Unknown role name.")
            return

        await ctx.send(f"**{matched}**: {ROLE_INFO[matched]}")

    @botc.command(name="reveal")
    async def botc_reveal(self, ctx: commands.Context):
        """Show storyteller the full assignment list."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can use this.")
            return

        lines: List[str] = []
        for uid in game.players:
            member = ctx.guild.get_member(uid)
            name = member.display_name if member else f"Unknown ({uid})"
            role = game.roles.get(uid, "Unknown")
            lines.append(f"- {name}: {role}")

        ok = await self._dm_storyteller(
            ctx.guild,
            game.storyteller_id,
            "Assignments:\n" + "\n".join(lines),
        )
        if ok:
            await ctx.send("Sent assignments to storyteller DM.")
        else:
            await ctx.send("Could not DM storyteller. Check DM settings.")

    @botc.command(name="end")
    async def botc_end(self, ctx: commands.Context):
        """End and clear the current game."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can end this game.")
            return

        del self.games[ctx.guild.id]
        await ctx.send("Game ended and cleared.")

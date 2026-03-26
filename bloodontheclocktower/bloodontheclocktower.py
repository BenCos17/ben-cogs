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
    bot_players: Dict[int, str] = field(default_factory=dict)
    next_bot_id: int = 1
    vote_open: bool = False
    vote_target: Optional[int] = None
    votes_yes: Set[int] = field(default_factory=set)
    votes_no: Set[int] = field(default_factory=set)
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

    def _player_name(self, guild: discord.Guild, game: GameState, uid: int) -> str:
        if uid in game.bot_players:
            return game.bot_players[uid]
        member = guild.get_member(uid)
        return member.display_name if member else f"Unknown ({uid})"

    def _new_bot_player(self, game: GameState) -> Tuple[int, str]:
        bot_id = -game.next_bot_id
        game.next_bot_id += 1
        return bot_id, f"Bot {game.next_bot_id - 1}"

    def _resolve_target(self, guild: discord.Guild, game: GameState, target: str) -> Optional[int]:
        cleaned = target.strip()
        if cleaned.startswith("<@") and cleaned.endswith(">"):
            cleaned = cleaned.replace("<@", "").replace("!", "").replace(">", "")

        if cleaned.lstrip("-").isdigit():
            uid = int(cleaned)
            if uid in game.players:
                return uid

        lowered = cleaned.lower()
        matches: List[int] = []
        for uid in game.players:
            if uid in game.bot_players:
                name = game.bot_players[uid]
            else:
                member = guild.get_member(uid)
                if member is None:
                    continue
                name = member.display_name
            if name.lower() == lowered:
                matches.append(uid)

        if len(matches) == 1:
            return matches[0]
        return None

    def _is_evil(self, role_name: str) -> bool:
        return role_name in MINIONS or role_name in DEMONS

    def _reset_vote(self, game: GameState):
        game.vote_open = False
        game.vote_target = None
        game.votes_yes.clear()
        game.votes_no.clear()

    def _check_win_state(self, game: GameState) -> Optional[str]:
        alive_roles = [game.roles[uid] for uid in game.alive if uid in game.roles]
        alive_demons = [r for r in alive_roles if r in DEMONS]
        if not alive_demons:
            return "Good wins: all Demons are dead."

        evil_alive = sum(1 for r in alive_roles if self._is_evil(r))
        good_alive = len(alive_roles) - evil_alive
        if evil_alive >= good_alive:
            return "Evil wins: evil players equal or outnumber good players."
        return None

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

    async def _announce_cheat(self, guild: discord.Guild, game: GameState, detail: str):
        channel = guild.get_channel(game.channel_id)
        storyteller_name = self._player_name(guild, game, game.storyteller_id)
        if isinstance(channel, (discord.TextChannel, discord.Thread)):
            await channel.send(
                "Debug cheat notice: "
                f"{storyteller_name} used debug role access while being a player. {detail}"
            )

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
            name = self._player_name(ctx.guild, game, uid)
            state = "alive" if (not game.started or uid in game.alive) else "dead"
            tag = " (Storyteller)" if uid == game.storyteller_id else ""
            lines.append(f"- {name}: {state}{tag}")

        await ctx.send("Players:\n" + "\n".join(lines))

    @botc.command(name="addbots")
    async def botc_addbots(self, ctx: commands.Context, count: int):
        """Add AI bot players to the lobby."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active game.")
            return
        if game.started:
            await ctx.send("Add bots before starting the game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can add bots.")
            return
        if count <= 0:
            await ctx.send("Count must be greater than 0.")
            return

        space_left = 15 - len(game.players)
        to_add = min(count, space_left)
        if to_add <= 0:
            await ctx.send("Lobby is already at the 15-player maximum.")
            return

        added_names: List[str] = []
        for _ in range(to_add):
            uid, name = self._new_bot_player(game)
            game.bot_players[uid] = name
            game.players.append(uid)
            added_names.append(name)

        await ctx.send(
            f"Added {to_add} bot player(s): {', '.join(added_names)}. "
            f"Total players: {len(game.players)}"
        )

    @botc.command(name="clearbots")
    async def botc_clearbots(self, ctx: commands.Context):
        """Remove all AI bot players from the lobby."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active game.")
            return
        if game.started:
            await ctx.send("Cannot clear bots after game start.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can clear bots.")
            return

        bot_ids = set(game.bot_players.keys())
        if not bot_ids:
            await ctx.send("No bot players in the lobby.")
            return

        game.players = [uid for uid in game.players if uid not in bot_ids]
        game.bot_players.clear()
        await ctx.send(f"Removed all bot players. Total players: {len(game.players)}")

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
        bot_assignments: List[str] = []
        for uid in game.players:
            member = ctx.guild.get_member(uid)
            if not member:
                bot_assignments.append(f"- {self._player_name(ctx.guild, game, uid)}: {game.roles[uid]}")
                continue
            ok = await self._dm_role(member, game.roles[uid])
            if not ok:
                dm_failed.append(member.display_name)

        msg = "Game started. Night 1 begins now. Roles have been sent by DM."
        if dm_failed:
            msg += "\nCould not DM: " + ", ".join(dm_failed)
        msg += "\n`[p]botc reveal` sends assignment summary to storyteller DM only."
        await ctx.send(msg)

        if bot_assignments:
            await self._dm_storyteller(
                ctx.guild,
                game.storyteller_id,
                "Bot role assignments:\n" + "\n".join(bot_assignments),
            )

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
        self._reset_vote(game)
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
        self._reset_vote(game)
        await ctx.send(f"It is now **Night {game.day_number}**.")

    @botc.command(name="execute")
    async def botc_execute(self, ctx: commands.Context, *, target: str):
        """Open an execution vote for a nominated player."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can open execution votes.")
            return
        if game.phase != "day":
            await ctx.send("Execution votes can only be started during day phase.")
            return
        target_id = self._resolve_target(ctx.guild, game, target)
        if target_id is None:
            await ctx.send("Could not find that player. Use mention, ID, or exact name (e.g. Bot 1).")
            return
        if target_id not in game.alive:
            await ctx.send("That player is already dead.")
            return

        target_name = self._player_name(ctx.guild, game, target_id)
        self._reset_vote(game)
        game.vote_open = True
        game.vote_target = target_id

        # Auto-cast votes for alive bot players to support bot-heavy lobbies.
        auto_yes = 0
        auto_no = 0
        for uid in list(game.alive):
            if uid == target_id or uid not in game.bot_players:
                continue
            if random.random() < 0.5:
                game.votes_yes.add(uid)
                auto_yes += 1
            else:
                game.votes_no.add(uid)
                auto_no += 1

        await ctx.send(
            f"Execution vote opened for **{target_name}**. "
            "Alive players use `[p]botc vote yes` or `[p]botc vote no` then storyteller runs `[p]botc tally`."
        )
        if auto_yes or auto_no:
            await ctx.send(f"Auto bot votes applied: {auto_yes} yes, {auto_no} no.")

    @botc.command(name="vote")
    async def botc_vote(self, ctx: commands.Context, choice: str):
        """Cast your vote on the active execution vote."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if game.phase != "day":
            await ctx.send("Voting is only available during day phase.")
            return
        if not game.vote_open or game.vote_target is None:
            await ctx.send("No active execution vote. Storyteller can start one with `[p]botc execute <target>`." )
            return
        if ctx.author.id not in game.alive:
            await ctx.send("Only alive players can vote.")
            return
        if ctx.author.id == game.vote_target:
            await ctx.send("Nominated player cannot vote on their own execution.")
            return

        normalized = choice.strip().lower()
        if normalized not in {"yes", "no", "y", "n"}:
            await ctx.send("Vote must be `yes` or `no`.")
            return

        game.votes_yes.discard(ctx.author.id)
        game.votes_no.discard(ctx.author.id)
        if normalized in {"yes", "y"}:
            game.votes_yes.add(ctx.author.id)
            await ctx.send(f"{ctx.author.mention} voted **YES**.")
        else:
            game.votes_no.add(ctx.author.id)
            await ctx.send(f"{ctx.author.mention} voted **NO**.")

    @botc.command(name="tally")
    async def botc_tally(self, ctx: commands.Context):
        """Close and resolve the current execution vote."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can tally votes.")
            return
        if not game.vote_open or game.vote_target is None:
            await ctx.send("No active execution vote.")
            return

        target_id = game.vote_target
        target_name = self._player_name(ctx.guild, game, target_id)
        yes_count = len(game.votes_yes)
        no_count = len(game.votes_no)
        self._reset_vote(game)

        if yes_count > no_count and target_id in game.alive:
            game.alive.remove(target_id)
            role = game.roles.get(target_id, "Unknown")
            await ctx.send(f"Vote passed ({yes_count}-{no_count}). {target_name} is executed.")
            await self._dm_storyteller(
                ctx.guild,
                game.storyteller_id,
                f"Execution result: {target_name} was **{role}**.",
            )

            winner = self._check_win_state(game)
            if winner:
                await ctx.send(winner)
            return

        await ctx.send(f"Vote failed ({yes_count}-{no_count}). No execution.")

    @botc.command(name="kill")
    async def botc_kill(self, ctx: commands.Context, *, target: str):
        """Mark a player dead at night."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can kill players.")
            return
        target_id = self._resolve_target(ctx.guild, game, target)
        if target_id is None:
            await ctx.send("Could not find that player. Use mention, ID, or exact name (e.g. Bot 1).")
            return
        if target_id not in game.alive:
            await ctx.send("That player is already dead.")
            return

        game.alive.remove(target_id)
        target_name = self._player_name(ctx.guild, game, target_id)
        await ctx.send(f"{target_name} died in the night.")

        winner = self._check_win_state(game)
        if winner:
            await ctx.send(winner)

    @botc.command(name="aisteps")
    async def botc_aisteps(self, ctx: commands.Context, steps: int = 1):
        """Run AI actions for the current phase."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can run AI actions.")
            return
        if steps <= 0:
            await ctx.send("Steps must be greater than 0.")
            return

        max_steps = min(steps, 20)
        logs: List[str] = []

        for _ in range(max_steps):
            if game.phase == "day":
                candidates = [uid for uid in game.alive if uid != game.storyteller_id]
                if not candidates:
                    logs.append("No valid day execution targets.")
                    break
                target_id = random.choice(candidates)
                target_name = self._player_name(ctx.guild, game, target_id)
                voters = [uid for uid in game.alive if uid != target_id]
                yes_votes = 0
                no_votes = 0
                for _uid in voters:
                    if random.random() < 0.5:
                        yes_votes += 1
                    else:
                        no_votes += 1
                if yes_votes > no_votes:
                    game.alive.remove(target_id)
                    logs.append(f"Day AI vote passes ({yes_votes}-{no_votes}); executes {target_name}.")
                    await self._dm_storyteller(
                        ctx.guild,
                        game.storyteller_id,
                        f"AI execution role: {target_name} was **{game.roles.get(target_id, 'Unknown')}**.",
                    )
                else:
                    logs.append(f"Day AI vote fails ({yes_votes}-{no_votes}); no execution.")
            else:
                demon_ids = [
                    uid for uid in game.alive if game.roles.get(uid) in DEMONS
                ]
                if not demon_ids:
                    logs.append("No alive Demon to act at night.")
                    break
                candidates = [uid for uid in game.alive if uid not in demon_ids]
                if not candidates:
                    logs.append("No valid night kill targets.")
                    break
                target_id = random.choice(candidates)
                game.alive.remove(target_id)
                target_name = self._player_name(ctx.guild, game, target_id)
                logs.append(f"Night AI kills {target_name}.")

            winner = self._check_win_state(game)
            if winner:
                logs.append(winner)
                break

        await ctx.send("\n".join(logs))

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
            name = self._player_name(ctx.guild, game, uid)
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

    @botc.command(name="debugrole")
    async def botc_debugrole(self, ctx: commands.Context, *, target: str):
        """Debug: storyteller can peek a player's role by target name/id/mention."""
        game = self._get_game(ctx.guild.id)
        if not game or not game.started:
            await ctx.send("No active started game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can use debug role peek.")
            return

        target_id = self._resolve_target(ctx.guild, game, target)
        if target_id is None:
            await ctx.send("Could not find that player. Use mention, ID, or exact name (e.g. Bot 1).")
            return

        role = game.roles.get(target_id, "Unknown")
        target_name = self._player_name(ctx.guild, game, target_id)
        ok = await self._dm_storyteller(
            ctx.guild,
            game.storyteller_id,
            f"Debug role peek: {target_name} is **{role}**.",
        )
        if not ok:
            await ctx.send("Could not DM storyteller. Check DM settings.")
            return

        await ctx.send("Debug role sent to storyteller DM.")

        # If storyteller is also in the player list, this is a deliberate cheat disclosure.
        if game.storyteller_id in game.players:
            await self._announce_cheat(
                ctx.guild,
                game,
                f"Peeked role for {target_name}.",
            )

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

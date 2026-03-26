import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import discord
from redbot.core import commands

from .data import (
    DEMONS,
    MEZEPHELES_WORDS,
    MINIONS,
    OUTSIDERS,
    ROLE_DISTRIBUTION,
    ROLE_INFO,
    TOWNSFOLK,
)


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
    first_night_no_kill_used: bool = False
    ai_chat_enabled: bool = True
    suspicion: Dict[int, float] = field(default_factory=dict)
    last_ai_chat_ts: float = 0.0
    turned_evil: Set[int] = field(default_factory=set)
    mezepheles_word: Optional[str] = None
    mezepheles_triggered: bool = False
    mezepheles_pending_convert: Optional[int] = None
    night_deaths: List[int] = field(default_factory=list)
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

    def _is_evil_player(self, game: GameState, uid: int) -> bool:
        if uid in game.turned_evil:
            return True
        return self._is_evil(game.roles.get(uid, ""))

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

        evil_alive = sum(1 for uid in game.alive if self._is_evil_player(game, uid))
        good_alive = len(game.alive) - evil_alive
        if evil_alive > good_alive:
            return "Evil wins: evil players outnumber good players."
        return None

    def _bot_vote_yes(self, game: GameState, voter_id: int, target_id: int) -> bool:
        target_is_evil = self._is_evil_player(game, target_id)
        voter_is_evil = self._is_evil_player(game, voter_id)
        suspicion = game.suspicion.get(target_id, 0.0)

        if voter_is_evil:
            yes_prob = 0.75 if not target_is_evil else 0.25
        else:
            yes_prob = 0.70 if target_is_evil else 0.30

        # Public suspicion influences votes, but alignment still dominates behavior.
        yes_prob += max(-0.2, min(0.2, suspicion * 0.08))
        yes_prob = max(0.05, min(0.95, yes_prob))
        return random.random() < yes_prob

    def _pick_ai_day_target(self, game: GameState) -> Optional[int]:
        candidates = [uid for uid in game.alive if uid != game.storyteller_id]
        if not candidates:
            return None

        # Slightly bias nominations toward evil, with enough noise to stay imperfect.
        weights: List[float] = []
        for uid in candidates:
            base = 1.6 if self._is_evil_player(game, uid) else 1.0
            suspicion_boost = max(0.0, game.suspicion.get(uid, 0.0))
            weights.append(base + suspicion_boost)
        return random.choices(candidates, weights=weights, k=1)[0]

    def _pick_ai_night_target(self, game: GameState, demon_ids: List[int]) -> Optional[int]:
        candidates = [uid for uid in game.alive if uid not in demon_ids]
        if not candidates:
            return None

        weights: List[float] = []
        for uid in candidates:
            target_is_evil = self._is_evil_player(game, uid)
            # Demons prefer good targets and often remove trusted voices.
            base = 0.35 if target_is_evil else 1.5
            suspicion = game.suspicion.get(uid, 0.0)
            trust_bonus = 0.8 if suspicion < 0 else 0.0
            weights.append(max(0.05, base + trust_bonus - (0.2 * max(0.0, suspicion))))

        return random.choices(candidates, weights=weights, k=1)[0]

    def _adjust_suspicion(self, game: GameState, uid: int, delta: float):
        current = game.suspicion.get(uid, 0.0)
        game.suspicion[uid] = max(-2.0, min(4.0, current + delta))

    def _extract_message_targets(
        self,
        guild: discord.Guild,
        game: GameState,
        content: str,
        mention_ids: Set[int],
    ) -> Set[int]:
        targets: Set[int] = set(mention_ids)
        lowered = content.lower()
        for uid in game.alive:
            if uid in game.bot_players:
                name = game.bot_players[uid].lower()
            else:
                member = guild.get_member(uid)
                if member is None:
                    continue
                name = member.display_name.lower()
            if name and name in lowered:
                targets.add(uid)
        return targets

    def _apply_message_inference(self, guild: discord.Guild, game: GameState, message: discord.Message):
        if message.author.id not in game.players:
            return

        text = message.content.lower()
        if not text.strip():
            return

        accuse_words = {"evil", "sus", "suspicious", "demon", "minion", "lying", "liar", "execute", "vote"}
        defend_words = {"good", "trust", "innocent", "clear", "safe", "town"}
        self_claim_words = {"i am", "i'm", "im", "my role", "trust me"}

        mention_ids = {member.id for member in message.mentions if member.id in game.players}
        targets = self._extract_message_targets(guild, game, message.content, mention_ids)
        targets.discard(message.author.id)

        has_accuse = any(w in text for w in accuse_words)
        has_defend = any(w in text for w in defend_words)

        if targets:
            delta = 0.0
            if has_accuse:
                delta += 0.55
            if has_defend:
                delta -= 0.45
            if delta != 0.0:
                for uid in targets:
                    self._adjust_suspicion(game, uid, delta)

        if any(w in text for w in self_claim_words):
            # Self-claims slightly increase suspicion to avoid free trust.
            self._adjust_suspicion(game, message.author.id, 0.15)

        if (
            game.mezepheles_word
            and not game.mezepheles_triggered
            and game.mezepheles_pending_convert is None
            and game.mezepheles_word.lower() in text
            and message.author.id in game.alive
            and not self._is_evil_player(game, message.author.id)
        ):
            game.mezepheles_pending_convert = message.author.id

    def _build_ai_chat_line(self, guild: discord.Guild, game: GameState) -> Optional[str]:
        alive_bots = [uid for uid in game.alive if uid in game.bot_players]
        if not alive_bots:
            return None

        speaker_id = random.choice(alive_bots)
        speaker_name = self._player_name(guild, game, speaker_id)
        candidates = [uid for uid in game.alive if uid != speaker_id]
        if not candidates:
            return None

        top_target = max(candidates, key=lambda uid: game.suspicion.get(uid, 0.0))
        target_name = self._player_name(guild, game, top_target)
        suspicion = game.suspicion.get(top_target, 0.0)

        if suspicion >= 1.0:
            templates = [
                f"{speaker_name}: I don't trust {target_name} right now.",
                f"{speaker_name}: {target_name} feels like the best execution today.",
                f"{speaker_name}: My read is that {target_name} is likely evil.",
            ]
        elif suspicion <= -0.5:
            templates = [
                f"{speaker_name}: I think {target_name} is probably good.",
                f"{speaker_name}: I'd rather not execute {target_name} today.",
                f"{speaker_name}: {target_name} sounds more trustworthy to me.",
            ]
        else:
            templates = [
                f"{speaker_name}: I'm still unsure. Need more info before voting.",
                f"{speaker_name}: Not convinced yet, can we hear more claims?",
                f"{speaker_name}: I want to compare stories before we execute.",
            ]
        return random.choice(templates)

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

    async def _send_ctx(self, ctx: commands.Context, message: str, *, ephemeral: bool = False):
        if ephemeral and getattr(ctx, "interaction", None) is not None:
            await ctx.send(message, ephemeral=True)
            return
        await ctx.send(message)

    @commands.hybrid_group(name="botc")
    @commands.guild_only()
    async def botc(self, ctx: commands.Context):
        """Blood on the Clocktower commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        game = self._get_game(message.guild.id)
        if not game or not game.started:
            return
        if not game.ai_chat_enabled or message.channel.id != game.channel_id:
            return
        if message.author.id not in game.players:
            return

        content = message.content.strip()
        if not content:
            return

        valid_prefixes = await self.bot.get_valid_prefixes(message.guild)
        if any(content.startswith(prefix) for prefix in valid_prefixes):
            return

        self._apply_message_inference(message.guild, game, message)

        if game.mezepheles_pending_convert == message.author.id:
            game.mezepheles_triggered = True
            player_name = self._player_name(message.guild, game, message.author.id)
            await self._dm_storyteller(
                message.guild,
                game.storyteller_id,
                f"Mezepheles trigger: {player_name} said the secret word and will become evil tonight.",
            )

        if game.phase != "day":
            return
        if time.time() - game.last_ai_chat_ts < 10:
            return
        if random.random() >= 0.35:
            return

        line = self._build_ai_chat_line(message.guild, game)
        if line:
            game.last_ai_chat_ts = time.time()
            await message.channel.send(line)

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
        game.first_night_no_kill_used = False
        game.suspicion = {uid: 0.0 for uid in game.players}
        game.last_ai_chat_ts = 0.0
        game.turned_evil.clear()
        game.mezepheles_word = None
        game.mezepheles_triggered = False
        game.mezepheles_pending_convert = None
        game.night_deaths.clear()

        dm_failed: List[str] = []
        for uid in game.players:
            member = ctx.guild.get_member(uid)
            if not member:
                continue
            ok = await self._dm_role(member, game.roles[uid])
            if not ok:
                dm_failed.append(member.display_name)

        mez_players = [uid for uid in game.players if game.roles.get(uid) == "Mezepheles"]
        if mez_players:
            game.mezepheles_word = random.choice(MEZEPHELES_WORDS)
            for mez_uid in mez_players:
                mez_member = ctx.guild.get_member(mez_uid)
                if mez_member:
                    try:
                        await mez_member.send(
                            f"Your Mezepheles secret word is **{game.mezepheles_word}**. "
                            "The first good player to say it becomes evil tonight."
                        )
                    except discord.Forbidden:
                        pass

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
        self._reset_vote(game)
        await ctx.send(f"It is now **Day {game.day_number}**.")

        if game.night_deaths:
            names = [self._player_name(ctx.guild, game, uid) for uid in game.night_deaths]
            if len(names) == 1:
                await ctx.send(f"At dawn, **{names[0]}** died in the night.")
            else:
                await ctx.send("At dawn, the following players died in the night: " + ", ".join(names))
            game.night_deaths.clear()
        else:
            await ctx.send("At dawn, nobody died in the night.")

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

        if game.mezepheles_pending_convert is not None:
            convert_uid = game.mezepheles_pending_convert
            game.mezepheles_pending_convert = None
            if convert_uid in game.alive and not self._is_evil_player(game, convert_uid):
                game.turned_evil.add(convert_uid)
                converted_name = self._player_name(ctx.guild, game, convert_uid)
                await self._dm_storyteller(
                    ctx.guild,
                    game.storyteller_id,
                    f"Mezepheles effect: {converted_name} has turned evil tonight.",
                )
                convert_member = ctx.guild.get_member(convert_uid)
                if convert_member:
                    try:
                        await convert_member.send("A dark influence takes hold. You are now evil.")
                    except discord.Forbidden:
                        pass

        await ctx.send(f"It is now **Night {game.day_number}**.")

    @botc.command(name="aichat")
    async def botc_aichat(self, ctx: commands.Context, enabled: bool):
        """Enable or disable AI chat reactions to player messages."""
        game = self._get_game(ctx.guild.id)
        if not game:
            await ctx.send("No active game.")
            return
        if not self._is_storyteller(game, ctx.author.id):
            await ctx.send("Only the storyteller can change AI chat settings.")
            return

        game.ai_chat_enabled = enabled
        state = "enabled" if enabled else "disabled"
        await ctx.send(f"AI chat reactions are now {state}.")

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
            if self._bot_vote_yes(game, uid, target_id):
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
            game.suspicion.pop(target_id, None)
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
        """Mark a player dead at night silently (storyteller/private log)."""
        await self._kill_player(ctx, target=target, announce=False)

    @botc.command(name="killpublic")
    async def botc_killpublic(self, ctx: commands.Context, *, target: str):
        """Mark a player dead at night and announce it publicly."""
        await self._kill_player(ctx, target=target, announce=True)

    async def _kill_player(self, ctx: commands.Context, *, target: str, announce: bool):
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
        game.suspicion.pop(target_id, None)
        target_name = self._player_name(ctx.guild, game, target_id)

        role = game.roles.get(target_id, "Unknown")
        await self._dm_storyteller(
            ctx.guild,
            game.storyteller_id,
            f"Night kill recorded: {target_name} ({role}).",
        )

        if announce:
            await ctx.send(f"{target_name} died in the night.")
        else:
            if target_id not in game.night_deaths:
                game.night_deaths.append(target_id)
            await self._send_ctx(ctx, "Night kill recorded.", ephemeral=True)

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
                target_id = self._pick_ai_day_target(game)
                if target_id is None:
                    logs.append("No valid day execution targets.")
                    break
                target_name = self._player_name(ctx.guild, game, target_id)
                voters = [uid for uid in game.alive if uid != target_id]
                yes_votes = 0
                no_votes = 0
                for voter_id in voters:
                    if self._bot_vote_yes(game, voter_id, target_id):
                        yes_votes += 1
                    else:
                        no_votes += 1
                if yes_votes > no_votes:
                    game.alive.remove(target_id)
                    game.suspicion.pop(target_id, None)
                    logs.append(f"Day AI vote passes ({yes_votes}-{no_votes}); executes {target_name}.")
                    await self._dm_storyteller(
                        ctx.guild,
                        game.storyteller_id,
                        f"AI execution role: {target_name} was **{game.roles.get(target_id, 'Unknown')}**.",
                    )
                else:
                    logs.append(f"Day AI vote fails ({yes_votes}-{no_votes}); no execution.")
            else:
                if game.day_number == 1 and not game.first_night_no_kill_used:
                    game.first_night_no_kill_used = True
                    logs.append("Night 1 protection: no AI night kill this night.")
                    continue

                demon_ids = [
                    uid for uid in game.alive if game.roles.get(uid) in DEMONS
                ]
                if not demon_ids:
                    logs.append("No alive Demon to act at night.")
                    break
                target_id = self._pick_ai_night_target(game, demon_ids)
                if target_id is None:
                    logs.append("No valid night kill targets.")
                    break
                game.alive.remove(target_id)
                game.suspicion.pop(target_id, None)
                target_name = self._player_name(ctx.guild, game, target_id)
                if target_id not in game.night_deaths:
                    game.night_deaths.append(target_id)
                logs.append("Night AI kill recorded.")
                await self._dm_storyteller(
                    ctx.guild,
                    game.storyteller_id,
                    f"AI night kill target: {target_name}.",
                )

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
            await self._send_ctx(ctx, "Sent assignments to storyteller DM.", ephemeral=True)
        else:
            await self._send_ctx(ctx, "Could not DM storyteller. Check DM settings.", ephemeral=True)

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
            await self._send_ctx(ctx, "Could not DM storyteller. Check DM settings.", ephemeral=True)
            return

        await self._send_ctx(ctx, "Debug role sent to storyteller DM.", ephemeral=True)

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

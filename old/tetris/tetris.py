import discord
from redbot.core import commands, tasks
import random

class TetrisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.command()
    async def tetris(self, ctx):
        if ctx.author.id in self.active_games:
            await ctx.send("You're already in a game!")
            return
        
        self.active_games[ctx.author.id] = TetrisGame(ctx)
        await self.active_games[ctx.author.id].start_game()

    @commands.command()
    async def tetris_left(self, ctx):
        await self._move_piece(ctx.author.id, "left")

    @commands.command()
    async def tetris_right(self, ctx):
        await self._move_piece(ctx.author.id, "right")

    @commands.command()
    async def tetris_rotate(self, ctx):
        await self._move_piece(ctx.author.id, "rotate")

    @commands.command()
    async def tetris_drop(self, ctx):
        await self._move_piece(ctx.author.id, "drop")

    async def _move_piece(self, player_id, action):
        if player_id in self.active_games:
            game = self.active_games[player_id]
            await game.move_piece(action)

    @tasks.loop(seconds=1.0)
    async def tetris_update_loop(self):
        for player_id, game in list(self.active_games.items()):
            if game.is_game_over():
                del self.active_games[player_id]
                continue
            await game.update()

class TetrisGame:
    def __init__(self, ctx):
        self.ctx = ctx
        self.board_width = 10
        self.board_height = 20
        self.board = [[' ' for _ in range(self.board_width)] for _ in range(self.board_height)]
        self.current_piece = None
        self.game_over = False

    async def start_game(self):
        # Initialize game
        self.current_piece = TetrisPiece()
        await self.update()

    async def update(self):
        # Clear the board
        self.board = [[' ' for _ in range(self.board_width)] for _ in range(self.board_height)]

        # Draw current piece
        if self.current_piece:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        self.board[self.current_piece.y + y][self.current_piece.x + x] = 'X'

        # Draw board
        board_str = '\n'.join([''.join(row) for row in self.board])
        await self.ctx.send(f"```\n{board_str}\n```")

    async def move_piece(self, action):
        if self.current_piece and not self.game_over:
            if action == "left":
                self.current_piece.move_left()
            elif action == "right":
                self.current_piece.move_right()
            elif action == "rotate":
                self.current_piece.rotate()
            elif action == "drop":
                self.current_piece.drop()

            await self.update()

    def is_game_over(self):
        return self.game_over

class TetrisPiece:
    SHAPES = [
        [[1, 1, 1, 1]],  # I
        [[1, 1], [1, 1]],  # O
        [[1, 0, 0], [1, 1, 1]],  # T
        [[0, 0, 1], [1, 1, 1]],  # L
        [[1, 0, 0], [1, 1, 1]],  # J
        [[0, 1, 0], [1, 1, 1]],  # S
        [[1, 1, 0], [0, 1, 1]]   # Z
    ]

    def __init__(self):
        self.shape = random.choice(self.SHAPES)
        self.x = 3
        self.y = 0

    def rotate(self):
        self.shape = list(zip(*self.shape[::-1]))

    def move_left(self):
        self.x -= 1

    def move_right(self):
        self.x += 1

    def drop(self):
        self.y += 1

def setup(bot):
    bot.add_cog(TetrisCog(bot))

from redbot.core import commands
import discord
import sympy


class LaTeXNotation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled_channels = set()  # Set to store enabled channels

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id in self.enabled_channels:
            latex_message = await self.convert_to_latex(message.content)
            if latex_message != message.content:
                await message.channel.send(latex_message)

    async def convert_to_latex(self, message_content):
        # Check if the message contains a mathematical expression
        if sympy.sympify(message_content, evaluate=False):
            try:
                # Use sympy to convert the expression to LaTeX notation
                expr = sympy.sympify(message_content, evaluate=False)
                latex_content = sympy.latex(expr)
                return latex_content
            except:
                pass

        return message_content

    @commands.command()
    async def latexon(self, ctx):
        """Enable LaTeX notation conversion in the current channel."""
        channel_id = ctx.channel.id
        self.enabled_channels.add(channel_id)
        await ctx.send("LaTeX notation conversion enabled.")

    @commands.command()
    async def latexoff(self, ctx):
        """Disable LaTeX notation conversion in the current channel."""
        channel_id = ctx.channel.id
        self.enabled_channels.remove(channel_id)
        await ctx.send("LaTeX notation conversion disabled.")

    def cog_unload(self):
        for channel_id in self.enabled_channels:
            self.enabled_channels.remove(channel_id)


def setup(bot):
    bot.add_cog(LaTeXNotation(bot))

import csv
from redbot.core import commands
import discord

class CSVParse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="parsecsv", help="Parses a CSV file and returns it in a more readable format")
    async def parse_csv(self, ctx, *, file: str):
        if file.endswith(".csv"):
            try:
                with open(file, 'r') as f:
                    csv_data = list(csv.reader(f))
                formatted_data = "```\n"
                for row in csv_data:
                    formatted_data += ",".join(row) + "\n"
                formatted_data += "```"
                if len(formatted_data) > 2000:
                    with open("output.csv", "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerows(csv_data)
                    file = discord.File("output.csv", filename="output.csv")
                    await ctx.send("The output is too large to be sent as a message. Here is the file instead:", file=file)
                else:
                    await ctx.send(formatted_data)
            except FileNotFoundError:
                await ctx.send("The file was not found. Please make sure the file is in the same directory as the bot.")
        else:
            await ctx.send("Please upload a CSV file.")



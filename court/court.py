from redbot.core import commands, data_manager
import discord

class Court(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cases = data_manager.cog_data(self)

    def save_cases(self):
        data_manager.save_cog_data(self)

    @commands.command()
    async def create_case(self, ctx, case_name):
        if case_name not in self.cases:
            self.cases[case_name] = {
                'judge': None,
                'plaintiff': None,
                'defendant': None,
                'witnesses': [],
                'evidence': [],
                'proceedings': [],
            }
            self.save_cases()  # Save data after modification
            await ctx.send(f"Case '{case_name}' created!")
        else:
            await ctx.send("Case already exists!")

    @commands.command()
    async def assign_role(self, ctx, role_name, member: discord.Member):
        case_name = ctx.channel.name
        if case_name in self.cases:
            if role_name in self.cases[case_name]:
                self.cases[case_name][role_name] = member
                self.save_cases()  # Save data after modification
                await ctx.send(f"{member.mention} assigned as {role_name}.")
            else:
                await ctx.send("Invalid role!")
        else:
            await ctx.send("Case does not exist!")

    @commands.command()
    async def add_witness(self, ctx, witness: discord.Member):
        case_name = ctx.channel.name
        if case_name in self.cases:
            self.cases[case_name]['witnesses'].append(witness)
            self.save_cases()  # Save data after modification
            await ctx.send(f"{witness.mention} added as a witness.")
        else:
            await ctx.send("Case does not exist!")

    @commands.command()
    async def add_evidence(self, ctx, evidence):
        case_name = ctx.channel.name
        if case_name in self.cases:
            self.cases[case_name]['evidence'].append(evidence)
            self.save_cases()  # Save data after modification
            await ctx.send("Evidence added to the case.")
        else:
            await ctx.send("Case does not exist!")

    @commands.command()
    async def present_case(self, ctx):
        case_name = ctx.channel.name
        if case_name in self.cases:
            case_details = self.cases[case_name]
            embed = discord.Embed(title=f"Case Details for '{case_name}'", color=discord.Color.blurple())
            embed.add_field(name="Judge", value=case_details['judge'] if case_details['judge'] else "Not assigned")
            embed.add_field(name="Plaintiff", value=case_details['plaintiff'] if case_details['plaintiff'] else "Not assigned")
            embed.add_field(name="Defendant", value=case_details['defendant'] if case_details['defendant'] else "Not assigned")
            embed.add_field(name="Proceedings", value=', '.join(case_details['proceedings']))
            embed.add_field(name="Evidence", value=', '.join(case_details['evidence']))
            embed.add_field(name="Witnesses", value=', '.join([w.mention for w in case_details['witnesses']]))
            await ctx.send(embed=embed)
        else:
            await ctx.send("Case does not exist!")

    # Add other commands similarly...

    @commands.command()
    async def start_proceedings(self, ctx):
        case_name = ctx.channel.name
        if case_name in self.cases:
            self.cases[case_name]['proceedings'].append("Case proceedings started.")
            self.save_cases()  # Save data after modification
            await ctx.send("Proceedings started.")
        else:
            await ctx.send("Case does not exist!")

    @commands.command()
    async def adjourn_case(self, ctx):
        case_name = ctx.channel.name
        if case_name in self.cases:
            self.cases[case_name]['proceedings'].append("Case adjourned.")
            self.save_cases()  # Save data after modification
            await ctx.send("Case adjourned.")
        else:
            await ctx.send("Case does not exist!")

    @commands.command()
    async def add_statement(self, ctx, *, statement):
        case_name = ctx.channel.name
        if case_name in self.cases:
            role = None
            for key, value in self.cases[case_name].items():
                if value == ctx.author:
                    role = key
                    break
            if role:
                self.cases[case_name]['proceedings'].append(f"{role} says: {statement}")
                self.save_cases()  # Save data after modification
                await ctx.send("Statement added to proceedings.")
            else:
                await ctx.send("You are not associated with this case!")
        else:
            await ctx.send("Case does not exist!")

    @commands.command()
    async def render_verdict(self, ctx, verdict):
        case_name = ctx.channel.name
        if case_name in self.cases:
            self.cases[case_name]['verdict'] = verdict
            self.save_cases()  # Save data after modification
            await ctx.send(f"Verdict '{verdict}' rendered for the case.")
        else:
            await ctx.send("Case does not exist!")


    def cog_unload(self):
        self.save_cases()  # Save data when the cog is unloaded

    def save_cases(self):
        data_manager.save_cog_data(self)

def setup(bot):
    bot.add_cog(Court(bot))

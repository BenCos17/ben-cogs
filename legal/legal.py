from redbot.core import commands

class Legal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roles = {
            "judge": None,
            "plaintiff": None,
            "defendant": None,
            "prosecutor": None,
            "defense": None,
            "witness": [],
            "jury": [],
        }
        self.role_lock = False  # To prevent accidental role acting
        self.session_active = False

    @commands.command()
    async def join(self, ctx, role: str):
        """Join a role in the court."""
        if self.role_lock:
            await ctx.send("Role assignment is currently locked.")
            return

        role = role.lower()
        if role not in self.roles:
            await ctx.send("Invalid role.")
            return

        if role == "witness" or role == "jury":
            if len(self.roles[role]) >= 12:
                await ctx.send(f"All {role}s slots are filled.")
                return
            self.roles[role].append(ctx.author.name)
        else:
            if self.roles[role] is not None:
                await ctx.send(f"{role.capitalize()} role is already taken.")
                return
            self.roles[role] = ctx.author.name

        await ctx.send(f"{ctx.author.mention} has joined as {role}.")

    @commands.command()
    async def leave(self, ctx):
        """Leave the court."""
        if self.role_lock:
            await ctx.send("Role assignment is currently locked.")
            return

        left_role = None
        for role, user in self.roles.items():
            if user == ctx.author.name:
                left_role = role
                self.roles[role] = None
                break

        if left_role is not None:
            await ctx.send(f"{ctx.author.mention} has left the {left_role} role.")
        else:
            await ctx.send(f"{ctx.author.mention} is not part of any role.")

    @commands.command()
    async def lock(self, ctx):
        """Lock role assignments to prevent accidental acting."""
        if self.role_lock:
            await ctx.send("Role assignment is already locked.")
        else:
            self.role_lock = True
            await ctx.send("Role assignment is now locked.")

    @commands.command()
    async def unlock(self, ctx):
        """Unlock role assignments to allow role changes."""
        if not self.role_lock:
            await ctx.send("Role assignment is already unlocked.")
        else:
            self.role_lock = False
            await ctx.send("Role assignment is now unlocked.")

    @commands.command()
    async def start_session(self, ctx):
        """Start a court session."""
        if self.session_active:
            await ctx.send("A court session is already in progress.")
            return

        if not self._check_roles_filled():
            await ctx.send("All roles must be filled before starting a session.")
            return

        self.session_active = True
        await ctx.send("Court session has started.")

        try:
            # Run the court session logic
            await self._run_court_session(ctx)
        except Exception as e:
            await ctx.send(f"An error occurred during the court session: {str(e)}")

        self.session_active = False
        await ctx.send("Court session has ended.")

    @commands.command()
    async def end_session(self, ctx):
        """End the current court session."""
        if not self.session_active:
            await ctx.send("No court session is currently active.")
            return

        self.session_active = False
        await ctx.send("Court session has been forcibly ended.")

    async def _run_court_session(self, ctx):
        """Run the court session logic."""
        judge = self.roles["judge"]
        plaintiff = self.roles["plaintiff"]
        defendant = self.roles["defendant"]
        prosecutor = self.roles["prosecutor"]
        defense = self.roles["defense"]
        witnesses = self.roles["witness"]
        jury = self.roles["jury"]

        await ctx.send("Opening statements begin.")

        await ctx.send(f"{judge} presiding over the court, please make your opening statement.")

        def check_role(member, role_name):
            return self.roles[role_name] == member

        await self.bot.wait_for("message", check=lambda m: check_role(m.author, "judge"))

        await ctx.send(f"{plaintiff}, please present your case.")

        await ctx.send(f"{plaintiff}, please state your arguments.")

        def check_role_or_witness(member):
            return self.roles["plaintiff"] == member or member in self.roles["witness"]

        await self.bot.wait_for("message", check=lambda m: check_role_or_witness(m.author))

        await ctx.send(f"{defendant}, your response.")

        def check_role_or_witness(member):
            return self.roles["defendant"] == member or member in self.roles["witness"]

        await self.bot.wait_for("message", check=lambda m: check_role_or_witness(m.author))

        await ctx.send(f"{prosecutor}, please present your arguments.")

        def check_role_or_witness(member):
            return self.roles["prosecutor"] == member or member in self.roles["witness"]

        await self.bot.wait_for("message", check=lambda m: check_role_or_witness(m.author))

        await ctx.send(f"{defense}, your counterarguments.")

        def check_role_or_witness(member):
            return self.roles["defense"] == member or member in self.roles["witness"]

        await self.bot.wait_for("message", check=lambda m: check_role_or_witness(m.author))

        await ctx.send("The witnesses will now be called to testify.")

        for witness in witnesses:
            await ctx.send(f"{witness}, please present your testimony.")

            def check_witness(member):
                return member == witness

            await self.bot.wait_for("message", check=lambda m: check_witness(m.author))

        await ctx.send("The jury will now deliberate.")

        def check_jury(member):
            return member in jury

        await self.bot.wait_for("message", check=lambda m: check_jury(m.author))

        await ctx.send("The jury has reached a verdict.")

        guilty_votes = 0
        not_guilty_votes = 0
        for jury_member in jury:
            await ctx.send(f"{jury_member}, please vote guilty or not guilty.")

            def check_jury_vote(member):
                return member == jury_member and member.content.lower() in ["guilty", "not guilty"]

            vote = await self.bot.wait_for("message", check=lambda m: check_jury_vote(m.author))
            vote_content = vote.content.lower()
            if vote_content == "guilty":
                guilty_votes += 1
            else:
                not_guilty_votes += 1

        if guilty_votes > not_guilty_votes:
            await ctx.send("The jury finds the defendant guilty.")
        else:
            await ctx.send("The jury finds the defendant not guilty.")

    def _check_roles_filled(self):
        """Check if all roles are filled."""
        for role, user in self.roles.items():
            if role != "witness" and role != "jury" and user is None:
                return False
        return True

def setup(bot):
    bot.add_cog(CourtSimulator(bot))

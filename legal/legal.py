from redbot.core import commands
import discord
import asyncio
import random

class Legal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}  # Dictionary to store player-role mappings

    @commands.command()
    async def trial(self, ctx):
        await ctx.send("Welcome to the legal trial simulation!")

        # Define the names of the different roles
        role_names = ["Judge", "Prosecution", "Defense", "Witness", "Jury"]

        # Prompt users to choose their roles
        for role in role_names:
            await ctx.send(f"Please choose a user for the role: {role}")
            user = await self.await_user(ctx)
            self.players[user.id] = role

        # Display the chosen roles
        await ctx.send("The chosen roles are:")
        for user, role in self.players.items():
            await ctx.send(f"{ctx.guild.get_member(user).mention}: {role}")

        # Opening statements
        await ctx.send("The trial is now in session.")
        await self.perform_action(ctx, 'Judge', "present the opening statement")
        await self.perform_action(ctx, 'Prosecution', "present the opening statement")

        # Witness testimonies
        await ctx.send(f"{self.get_role_mention('Prosecution')}, please call your first witness.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, you may cross-examine the witness.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, please call your first witness.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Prosecution')}, you may cross-examine the witness.")
        await self.await_user_response(ctx)

        # Presentation of evidence
        await ctx.send(f"{self.get_role_mention('Prosecution')}, please present your evidence.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, please present your evidence.")
        await self.await_user_response(ctx)

        # Closing arguments
        await ctx.send(f"{self.get_role_mention('Prosecution')}, please present your closing argument.")
        await self.await_user_response(ctx)

        await ctx.send(f"{self.get_role_mention('Defense')}, please present your closing argument.")
        await self.await_user_response(ctx)

        # Verdict
        await ctx.send(f"{self.get_role_mention('Judge')}, please deliver the verdict.")
        await self.await_user_response(ctx)

        await ctx.send("Thank you for participating in the legal trial simulation.")

    @commands.command()
    async def trial_ai(self, ctx):
        await ctx.send("Welcome to the AI-controlled legal trial simulation!")

        # Define the names of the different roles
        role_names = ["Judge", "Prosecution", "Defense", "Witness", "Jury"]

        # Assign roles to AI-controlled players
        for role in role_names:
            self.players[role] = "AI"

        # Display the chosen roles
        await ctx.send("The chosen roles are:")
        for role, user in self.players.items():
            await ctx.send(f"{role}: {user}")

        # Opening statements
        await ctx.send("The trial is now in session.")
        await self.perform_action(ctx, 'Judge', "present the opening statement")
        await self.perform_action(ctx, 'Prosecution', "present the opening statement")

        # Witness testimonies
        await ctx.send("The AI-controlled prosecution calls its first witness.")
        await self.await_user_response(ctx)

        await ctx.send("The AI-controlled defense may cross-examine the witness.")
        await self.await_user_response(ctx)

        await ctx.send("The AI-controlled defense calls its first witness.")
        await self.await_user_response(ctx)

        await ctx.send("The AI-controlled prosecution may cross-examine the witness.")
        await self.await_user_response(ctx)

        # Presentation of evidence
        await ctx.send("The AI-controlled prosecution presents its evidence.")
        await self.await_user_response(ctx)

        await ctx.send("The AI-controlled defense presents its evidence.")
        await self.await_user_response(ctx)

        # Closing arguments
        await ctx.send("The AI-controlled prosecution presents its closing argument.")
        await self.await_user_response(ctx)

        await ctx.send("The AI-controlled defense presents its closing argument.")
        await self.await_user_response(ctx)

        # Verdict
        await ctx.send("The AI-controlled judge delivers the verdict.")
        await self.await_user_response(ctx)

        await ctx.send("Thank you for participating in the AI-controlled legal trial simulation.")

    @commands.command()
    async def cancel_trial(self, ctx):
        await ctx.send("The trial simulation has been canceled.")
        self.players = {}  # Clear the player-role mappings

    async def await_user(self, ctx):
        try:
            def check(m):
                return (
                    m.author != self.bot.user
                    and m.channel == ctx.channel
                    and m.mentions  # Ensure the message mentions at least one user
                )

            msg = await self.bot.wait_for('message', check=check, timeout=300)
            user_mention = msg.mentions[0]  # Get the first mentioned user
            return user_mention
        except asyncio.TimeoutError:
            await ctx.send("Timeout: No response received. Ending trial simulation.")
            raise commands.CommandError("Simulation timeout.")

    async def await_user_response(self, ctx):
        try:
            def check(m):
                return m.author != self.bot.user and m.channel == ctx.channel

            response = await self.bot.wait_for('message', check=check, timeout=300)
            await ctx.send(response.content)  # Send the response to chat
        except asyncio.TimeoutError:
            await ctx.send("Timeout: No response received. Ending trial simulation.")
            raise commands.CommandError("Simulation timeout.")

    async def perform_action(self, ctx, role_name, action):
        if role_name in self.players:
            if self.players[role_name] == "AI":
                await ctx.send(f"The AI-controlled {role_name} will now {action}.")
                await asyncio.sleep(2)  # Simulating AI response time
            else:
                user_id = next((k for k, v in self.players.items() if v == role_name), None)
                if user_id:
                    user = ctx.guild.get_member(user_id)
                    await ctx.send(f"{user.mention}, please {action}.")
                    await self.await_user_response(ctx)
                else:
                    await ctx.send(f"Sorry, the role '{role_name}' is not assigned to any user.")
        else:
            await ctx.send(f"Sorry, the role '{role_name}' is not available in this trial.")

    def get_role_mention(self, role_name):
        role_id = next((k for k, v in self.players.items() if v == role_name), None)
        if role_id:
            return f"<@{role_id}>"
        return ""

    def generate_statement(self, statement_type):
        statements = {
            "opening_statement": [
                "Ladies and gentlemen of the jury, esteemed judge, and respected members of the court,",
                "Your Honor, honorable members of the jury, and distinguished opposing counsel,",
                "May it please the court, ladies and gentlemen of the jury, and honorable judge,",
                # Add more opening statements here...
            ],
            "witness_testimony": [
                "I swear to tell the truth, the whole truth, and nothing but the truth.",
                "Based on my observations and expertise in the field,",
                "As an eyewitness to the incident,",
                # Add more witness testimonies here...
            ],
            "cross_examination": [
                "Objection, Your Honor! The question is leading the witness.",
                "Please rephrase the question to allow the witness to answer without bias.",
                "I request that the witness's previous statement be stricken from the record.",
                # Add more cross-examination responses here...
            ],
            "evidence_presentation": [
                "I would like to present Exhibit A as evidence.",
                "This document clearly shows the defendant's involvement in the crime.",
                "I have a video recording that captures the incident as it happened.",
                # Add more evidence presentation responses here...
            ],
            "closing_argument": [
                "Ladies and gentlemen of the jury, the evidence presented before you speaks for itself.",
                "The defense's case lacks substantial evidence to support their claims.",
                "In light of the facts presented, the only reasonable verdict is guilty.",
                # Add more closing arguments here...
            ],
            "verdict": [
                "After careful consideration of the evidence and testimonies, I hereby find the defendant guilty.",
                "In light of the reasonable doubt presented, I find the defendant not guilty.",
                "The jury has reached a unanimous decision of guilty.",
                # Add more verdicts here...
            ],
        }

        if statement_type in statements:
            return random.choice(statements[statement_type])
        return ""

def setup(bot):
    bot.add_cog(Legal(bot))

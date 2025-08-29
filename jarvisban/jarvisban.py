import discord
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
import re

class JarvisBan(commands.Cog):
    """
    A cog that allows users to ban someone by saying "jarvis ban this guy"
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        # Default settings
        default_guild = {
            "enabled": False,
            "log_channel": None,
            "ban_reason": "Banned by Jarvis via 'jarvis ban this guy' command",
            "allow_bot_owner_override": False,
            "trigger_phrases": [
                "jarvis ban this guy",
                "jarvis ban this person",
                "jarvis ban them",
                "jarvis ban him",
                "jarvis ban her"
            ]
        }
        
        self.config.register_guild(**default_guild)
        
    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for 'jarvis ban this guy' messages"""
        if message.author.bot:
            return
            
        if not message.guild:
            return
            
        # Check if the cog is enabled for this guild
        if not await self.config.guild(message.guild).enabled():
            return
            
        # Check if the message contains the trigger phrase
        trigger_phrases = await self.config.guild(message.guild).trigger_phrases()
        
        message_content = message.content.lower().strip()
        
        # Check if the message starts with any EXACT trigger phrase (to avoid partial matches)
        if not any(message_content == phrase.lower() or message_content.startswith(phrase.lower() + " ") for phrase in trigger_phrases):
            return
            
        # Check if user has permission to ban - only proceed if they do
        # Bot owners can override this permission requirement
        if not message.author.guild_permissions.ban_members:
            # Check if user is bot owner and override is enabled
            if not (await self.bot.is_owner(message.author) and await self.config.guild(message.guild).allow_bot_owner_override()):
                return  # Silently ignore if no permission and not bot owner or override disabled
        
        # Find mentioned users
        if not message.mentions:
            await message.channel.send("❌ Please mention the user you want to ban!")
            return
            
        target_user = message.mentions[0]
        
        # Bot owners can bypass all permission checks
        if not await self.bot.is_owner(message.author):
            # Check if target can be banned (only for non-bot-owners)
            if target_user.top_role >= message.guild.me.top_role:
                await message.channel.send("❌ I cannot ban this user due to role hierarchy!")
                return
                
            if target_user.guild_permissions.administrator:
                await message.channel.send("❌ I cannot ban administrators!")
                return
            
        # First confirmation - ask if they really want to ban
        first_confirm = await message.channel.send(
            f"🤖 **Jarvis Ban Request**\n\n"
            f"**{message.author.display_name}** wants to ban **{target_user.display_name}**.\n"
            f"React with ✅ to proceed or ❌ to cancel."
        )
        
        # Add reaction options
        await start_adding_reactions(first_confirm, ["✅", "❌"])
        
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                timeout=30.0,
                check=ReactionPredicate.with_emojis(["✅", "❌"], first_confirm, message.author)
            )
            
            if str(reaction.emoji) == "✅":
                # Second confirmation - final confirmation
                final_confirm = await message.channel.send(
                    f"🤖 **Final Confirmation**\n\n"
                    f"Are you **absolutely sure** you want to ban **{target_user.display_name}**?\n"
                    f"This action cannot be undone!\n"
                    f"React with 🔴 to confirm ban or ❌ to cancel."
                )
                
                # Add reaction options for final confirmation
                await start_adding_reactions(final_confirm, ["🔴", "❌"])
                
                try:
                    final_reaction, final_user = await self.bot.wait_for(
                        "reaction_add",
                        timeout=30.0,
                        check=ReactionPredicate.with_emojis(["🔴", "❌"], final_confirm, message.author)
                    )
                    
                    if str(final_reaction.emoji) == "🔴":
                        # Proceed with ban
                        reason = await self.config.guild(message.guild).ban_reason()
                        
                        try:
                            await target_user.ban(reason=reason)
                            
                            # Send success message
                            embed = discord.Embed(
                                title="🤖 Jarvis Ban Successful",
                                description=f"**{target_user.display_name}** has been banned from the server.",
                                color=discord.Color.red(),
                                timestamp=discord.utils.utcnow()
                            )
                            embed.add_field(name="Banned by", value=message.author.mention, inline=True)
                            embed.add_field(name="Reason", value=reason, inline=True)
                            embed.set_footer(text="Jarvis Ban System")
                            
                            await message.channel.send(embed=embed)
                            
                            # Log the ban if log channel is set
                            log_channel_id = await self.config.guild(message.guild).log_channel()
                            if log_channel_id:
                                log_channel = message.guild.get_channel(log_channel_id)
                                if log_channel:
                                    log_embed = discord.Embed(
                                        title="🚫 User Banned via Jarvis",
                                        description=f"**{target_user.display_name}** was banned using the Jarvis ban system.",
                                        color=discord.Color.red(),
                                        timestamp=discord.utils.utcnow()
                                    )
                                    log_embed.add_field(name="User", value=f"{target_user} ({target_user.id})", inline=True)
                                    log_embed.add_field(name="Banned by", value=f"{message.author} ({message.author.id})", inline=True)
                                    log_embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                                    log_embed.add_field(name="Reason", value=reason, inline=False)
                                    
                                    await log_channel.send(embed=log_embed)
                                    
                        except discord.Forbidden:
                            await message.channel.send("❌ I don't have permission to ban users!")
                        except discord.HTTPException as e:
                            await message.channel.send(f"❌ An error occurred while banning: {e}")
                            
                    else:
                        await message.channel.send("❌ Ban cancelled at final confirmation.")
                        
                except TimeoutError:
                    await message.channel.send("⏰ Final confirmation timed out.")
                    
                # Clean up final confirmation message
                try:
                    await final_confirm.delete()
                except:
                    pass
                    
            else:
                await message.channel.send("❌ Ban cancelled at first confirmation.")
                
        except TimeoutError:
            await message.channel.send("⏰ First confirmation timed out.")
            
        # Clean up first confirmation message
        try:
            await first_confirm.delete()
        except:
            pass
    
    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def jarvisban(self, ctx):
        """Configure the Jarvis Ban system"""
        if not ctx.invoked_subcommand:
            await ctx.send_help()
    
    @jarvisban.command(name="enable")
    async def jarvisban_enable(self, ctx):
        """Enable the Jarvis Ban system"""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("✅ Jarvis Ban system has been enabled!")
    
    @jarvisban.command(name="disable")
    async def jarvisban_disable(self, ctx):
        """Disable the Jarvis Ban system"""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("❌ Jarvis Ban system has been disabled!")
    
    @jarvisban.command(name="logchannel")
    async def jarvisban_logchannel(self, ctx, channel: discord.TextChannel = None):
        """Set the log channel for Jarvis Ban actions"""
        if channel is None:
            await self.config.guild(ctx.guild).log_channel.set(None)
            await ctx.send("✅ Log channel has been disabled!")
        else:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(f"✅ Log channel set to {channel.mention}!")
    
    @jarvisban.command(name="reason")
    async def jarvisban_reason(self, ctx, *, reason: str):
        """Set the default ban reason for Jarvis Ban"""
        await self.config.guild(ctx.guild).ban_reason.set(reason)
        await ctx.send(f"✅ Default ban reason set to: {reason}")
    
    @jarvisban.command(name="addphrase")
    async def jarvisban_addphrase(self, ctx, *, phrase: str):
        """Add a new trigger phrase for the Jarvis Ban system"""
        current_phrases = await self.config.guild(ctx.guild).trigger_phrases()
        
        if phrase.lower() in [p.lower() for p in current_phrases]:
            await ctx.send("❌ That phrase already exists!")
            return
            
        current_phrases.append(phrase)
        await self.config.guild(ctx.guild).trigger_phrases.set(current_phrases)
        await ctx.send(f"✅ Added new trigger phrase: **{phrase}**")
    
    @jarvisban.command(name="removephrase")
    async def jarvisban_removephrase(self, ctx, *, phrase: str):
        """Remove a trigger phrase from the Jarvis Ban system"""
        current_phrases = await self.config.guild(ctx.guild).trigger_phrases()
        
        # Find the phrase (case-insensitive)
        phrase_lower = phrase.lower()
        found_phrase = None
        
        for p in current_phrases:
            if p.lower() == phrase_lower:
                found_phrase = p
                break
        
        if not found_phrase:
            await ctx.send("❌ That phrase doesn't exist!")
            return
            
        # Don't allow removing all phrases
        if len(current_phrases) <= 1:
            await ctx.send("❌ Cannot remove the last trigger phrase!")
            return
            
        current_phrases.remove(found_phrase)
        await self.config.guild(ctx.guild).trigger_phrases.set(current_phrases)
        await ctx.send(f"✅ Removed trigger phrase: **{found_phrase}**")
    
    @jarvisban.command(name="listphrases")
    async def jarvisban_listphrases(self, ctx):
        """List all current trigger phrases"""
        phrases = await self.config.guild(ctx.guild).trigger_phrases()
        
        if not phrases:
            await ctx.send("❌ No trigger phrases configured!")
            return
            
        embed = discord.Embed(
            title="🤖 Jarvis Ban Trigger Phrases",
            description="Current phrases that will trigger the ban system:",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        for i, phrase in enumerate(phrases, 1):
            embed.add_field(name=f"Phrase {i}", value=f"`{phrase}`", inline=False)
            
        embed.set_footer(text=f"Total: {len(phrases)} phrases")
        await ctx.send(embed=embed)
    
    @jarvisban.command(name="resetphrases")
    async def jarvisban_resetphrases(self, ctx):
        """Reset trigger phrases to default values"""
        default_phrases = [
            "jarvis ban this guy",
            "jarvis ban this person",
            "jarvis ban them",
            "jarvis ban him",
            "jarvis ban her"
        ]
        
        await self.config.guild(ctx.guild).trigger_phrases.set(default_phrases)
        await ctx.send("✅ Trigger phrases have been reset to default values!")
    
    @jarvisban.command(name="settings")
    async def jarvisban_settings(self, ctx):
        """Show current Jarvis Ban settings"""
        settings = await self.config.guild(ctx.guild).all()
        
        embed = discord.Embed(
            title="🤖 Jarvis Ban Settings",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="Status", 
            value="✅ Enabled" if settings["enabled"] else "❌ Disabled", 
            inline=True
        )
        embed.add_field(
            name="Permission Required", 
            value="✅ Always Required", 
            inline=True
        )
        
        log_channel_id = settings["log_channel"]
        if log_channel_id:
            log_channel = ctx.guild.get_channel(log_channel_id)
            log_channel_text = log_channel.mention if log_channel else "Unknown Channel"
        else:
            log_channel_text = "Not set"
            
        embed.add_field(name="Log Channel", value=log_channel_text, inline=True)
        embed.add_field(name="Ban Reason", value=settings["ban_reason"], inline=False)
        
        # Add trigger phrases info
        phrases = await self.config.guild(ctx.guild).trigger_phrases()
        phrases_text = f"`{phrases[0]}`" if len(phrases) == 1 else f"`{phrases[0]}` and {len(phrases)-1} more"
        embed.add_field(name="Trigger Phrases", value=phrases_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @jarvisban.command(name="test")
    async def jarvisban_test(self, ctx):
        """Test if the Jarvis Ban system is working"""
        enabled = await self.config.guild(ctx.guild).enabled()
        if enabled:
            await ctx.send("✅ Jarvis Ban system is enabled and working!")
        else:
            await ctx.send("❌ Jarvis Ban system is disabled!")

def setup(bot):
    """Add the cog to the bot"""
    bot.add_cog(JarvisBan(bot))

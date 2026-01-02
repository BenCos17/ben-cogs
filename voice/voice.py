from redbot.core import commands
import discord
import logging
import os
import time
import wave
import asyncio
import sys
from collections import defaultdict

try:
    import voice_recv
except Exception:
    # The package installs as `discord.ext.voice_recv`; prefer that if available
    try:
        from discord.ext import voice_recv  # type: ignore
    except Exception:
        voice_recv = None


class RecordingSink:
    """A minimal sink compatible with voice_recv.AudioSink API.

    This sink collects PCM chunks per user and writes them to WAV files on cleanup.
    Optionally it can upload the resulting files to a text channel and mention the
    user who requested the recording. Uploading is performed via the bot's event
    loop using a thread-safe scheduling call so cleanup can be called from a
    background thread.
    """

    def __init__(self, outdir: str = "voice_records", *, bot=None, text_channel_id: int | None = None, uploader_id: int | None = None, voice_channel_name: str | None = None, upload_on_cleanup: bool = False):
        # Keep lazy imports to avoid hard dependency for users who don't have the package
        self._has_voice_recv_audio_sink = hasattr(voice_recv, "AudioSink") if voice_recv else False
        if self._has_voice_recv_audio_sink:
            # Create an adapter subclass that implements the required abstract methods
            base = voice_recv.AudioSink
            class _Impl(base):
                def __init__(self, parent):
                    # Ensure base initialization runs if required
                    try:
                        super().__init__()
                    except Exception:
                        pass
                    self._parent = parent

                def wants_opus(self) -> bool:
                    return self._parent.wants_opus()

                def write(self, user, data) -> None:
                    return self._parent.write(user, data)

                def cleanup(self) -> None:
                    return self._parent.cleanup()

            # instantiate adapter with a reference back to this RecordingSink
            self._impl = _Impl(self)
        else:
            self._impl = None

        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok=True)
        self.buffers = defaultdict(list)  # user_id -> [bytes]
        self.sample_rate = 48000
        self.sample_width = 2
        self.channels = 1

        # Upload-related state
        self.bot = bot
        self.text_channel_id = text_channel_id
        self.uploader_id = uploader_id
        self.voice_channel_name = voice_channel_name
        self.upload_on_cleanup = bool(upload_on_cleanup)

    # Compatibility wrappers expected by voice_recv
    def wants_opus(self) -> bool:
        # We expect decoded PCM (so return False) — if you want opus, adjust
        return False

    def write(self, user, data) -> None:
        pcm = getattr(data, "pcm", None)
        if not pcm:
            # nothing to write (e.g., opus-only sink, or silence)
            return

        user_id = getattr(user, "id", "unknown")
        self.buffers[user_id].append(pcm)

    def cleanup(self) -> None:
        # Write out WAV files for each collected user
        written = []  # list of (user_id, filename)
        for uid, chunks in list(self.buffers.items()):
            if not chunks:
                continue
            filename = os.path.join(self.outdir, f"{uid}_{int(time.time())}.wav")
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.sample_width)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(chunks))
            written.append((uid, filename))

        # If configured, schedule an async upload back into the bot's loop
        if written and self.upload_on_cleanup and self.bot and self.text_channel_id:
            # Use run_coroutine_threadsafe because cleanup may be called from a non-async thread
            try:
                asyncio.run_coroutine_threadsafe(self._async_upload(written), self.bot.loop)
            except Exception:
                logging.getLogger("red.voice").exception("Failed to schedule upload of recordings")

    async def _async_upload(self, written: list[tuple[int, str]]) -> None:
        """Coroutine to send recordings to the configured text channel and mention the uploader."""
        logger = logging.getLogger("red.voice")
        try:
            channel = self.bot.get_channel(self.text_channel_id)
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(self.text_channel_id)
                except Exception:
                    channel = None

            if channel is None:
                logger.warning("Upload requested but text channel %s could not be found", self.text_channel_id)
                return

            mention = f"<@{self.uploader_id}>" if self.uploader_id else None
            vc_name = self.voice_channel_name or "(unknown)"
            content = f"{mention} recordings from voice channel {vc_name}:" if mention else f"Recordings from voice channel {vc_name}:"

            files = []
            for uid, path in written:
                try:
                    files.append(discord.File(path, filename=os.path.basename(path)))
                except Exception:
                    logger.exception("Failed to open recording file for upload: %s", path)

            if not files:
                await channel.send(content + "\nNo files available to upload.")
                return

            # Discord limits number/size of files — best effort upload
            await channel.send(content, files=files)
        except Exception:
            logger.exception("Unexpected error during upload of voice recordings")


class VoiceRecvCog(commands.Cog):
    """Cog that provides simple commands to join voice with a VoiceRecv client and record audio.

    Commands:
    - vjoin: Join your voice channel using voice_recv.VoiceRecvClient (requires package)
    - vleave: Disconnect from voice
    - vlisten [outdir]: Start listening and record per-user WAV files to `outdir` (default: voice_records)
    - vstop: Stop listening
    - vspeaking [member]: Show speaking state for a member
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("red.voice")
        self._sink = None

    @commands.command()
    async def vjoin(self, ctx: commands.Context) -> None:
        """Join the author's voice channel using VoiceRecvClient (requires discord-ext-voice-recv)."""
        if voice_recv is None:
            # Try a runtime import in case the package was installed after the cog was loaded
            try:
                import importlib
                try:
                    _mod = importlib.import_module("voice_recv")
                except Exception:
                    _mod = importlib.import_module("discord.ext.voice_recv")
                globals()["voice_recv"] = _mod
            except Exception:
                await ctx.send("discord-ext-voice-recv is not installed. Install it to use voice receive features (then reload the cog or restart the bot).")
                return

        channel = None
        if ctx.author and getattr(ctx.author, "voice", None):
            channel = ctx.author.voice.channel
        if channel is None:
            await ctx.send("You must be connected to a voice channel to use this command.")
            return

        # Use the provided client class
        cls = getattr(voice_recv, "VoiceRecvClient", None)
        if cls is None:
            await ctx.send("VoiceRecvClient class not found in voice_recv package.")
            return

        try:
            await channel.connect(cls=cls)
        except Exception as exc:
            self.logger.exception("Failed to connect to voice: %s", exc)
            await ctx.send(f"Failed to connect to voice: {exc}")
            return

        await ctx.send(f"Joined voice channel {channel.name}")

    @commands.command()
    async def vleave(self, ctx: commands.Context) -> None:
        """Disconnect from voice channel."""
        vc: discord.VoiceClient | None = ctx.voice_client
        if vc is None:
            await ctx.send("Not connected to voice.")
            return

        try:
            await vc.disconnect()
            await ctx.send("Disconnected from voice.")
        except Exception as exc:
            self.logger.exception("Failed to disconnect: %s", exc)
            await ctx.send(f"Failed to disconnect: {exc}")

    @commands.command()
    async def vlisten(self, ctx: commands.Context, outdir: str = "voice_records", upload: str = None) -> None:
        """Start listening and record per-user WAV files to `outdir` (default: voice_records).

        Pass the literal word `upload` as a second argument to automatically post
        the recordings to the text channel that invoked the command when
        recording finishes; the requesting user will be mentioned.
        """
        vc: discord.VoiceClient | None = ctx.voice_client
        if vc is None:
            await ctx.send("Bot is not connected to voice.")
            return

        if voice_recv is None:
            # Try a runtime import in case the package was installed after the cog was loaded
            try:
                import importlib
                try:
                    _mod = importlib.import_module("voice_recv")
                except Exception:
                    _mod = importlib.import_module("discord.ext.voice_recv")
                globals()["voice_recv"] = _mod
            except Exception:
                await ctx.send("discord-ext-voice-recv is not installed. Install it to use voice receive features (then reload the cog or restart the bot).")
                return

        if not hasattr(vc, "listen"):
            await ctx.send("This voice client does not support listening — make sure discord-ext-voice-recv is installed and used as the voice client (VoiceRecvClient).")
            return

        if self._sink is not None:
            await ctx.send("Already listening. Use `vstop` to stop the current recording.")
            return

        upload_flag = False
        if upload:
            upload_flag = str(upload).lower() in ("upload", "send", "true", "yes", "1")

        voice_channel_name = None
        if ctx.author and getattr(ctx.author, "voice", None):
            try:
                voice_channel_name = ctx.author.voice.channel.name
            except Exception:
                voice_channel_name = None

        sink = RecordingSink(
            outdir=outdir,
            bot=self.bot,
            text_channel_id=ctx.channel.id,
            uploader_id=getattr(ctx.author, "id", None),
            voice_channel_name=voice_channel_name,
            upload_on_cleanup=upload_flag,
        )

        def _after(exc):
            if exc:
                self.logger.exception("Recording finished with error: %s", exc)
            else:
                self.logger.info("Recording finished cleanly. Writing files.")
            try:
                sink.cleanup()
            except Exception:
                self.logger.exception("Error while cleaning up sink")

        try:
            to_listen = getattr(sink, "_impl", None) or sink
            vc.listen(to_listen, after=_after)
        except Exception as exc:
            self.logger.exception("Failed to start listening: %s", exc)
            await ctx.send(f"Failed to start listening: {exc}")
            return

        self._sink = sink
        msg = f"Started listening and will save recordings to {outdir}"
        if upload_flag:
            msg += ". Recordings will be uploaded to this channel when finished."
        await ctx.send(msg)

    @commands.command()
    async def vstop(self, ctx: commands.Context) -> None:
        """Stop listening and finalize recordings."""
        vc: discord.VoiceClient | None = ctx.voice_client
        if vc is None:
            await ctx.send("Not connected to voice.")
            return

        if self._sink is None:
            await ctx.send("Not currently listening.")
            return

        try:
            if hasattr(vc, "stop_listening"):
                vc.stop_listening()
            else:
                # Fallback: attempt to stop by stopping the socket reading
                try:
                    vc.stop()
                except Exception:
                    pass
        except Exception as exc:
            self.logger.exception("Failed to stop listening: %s", exc)
            await ctx.send(f"Failed to stop listening: {exc}")
            return

        # Ensure cleanup and write files
        try:
            self._sink.cleanup()
        except Exception:
            self.logger.exception("Error while cleaning up sink")

        self._sink = None
        await ctx.send("Stopped listening and finalized recordings.")

    @commands.command()
    async def vspeaking(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """Show speaking (voice activity indicator) state for a member. If no member is given, shows the author's state."""
        member = member or ctx.author
        vc: discord.VoiceClient | None = ctx.voice_client
        if vc is None:
            await ctx.send("Not connected to voice.")
            return

        if not hasattr(vc, "get_speaking"):
            await ctx.send("This voice client does not expose speaking state (not a VoiceRecvClient).")
            return

        try:
            state = vc.get_speaking(member)
        except Exception as exc:
            self.logger.exception("Error checking speaking state: %s", exc)
            await ctx.send(f"Error checking speaking state: {exc}")
            return

        await ctx.send(f"Speaking state for {member.display_name}: {state}")

    @commands.command()
    async def vcheck(self, ctx: commands.Context) -> None:
        """Check whether `voice_recv` is importable and show voice client capabilities."""
        try:
            import importlib
            try:
                mod = importlib.import_module("voice_recv")
            except Exception:
                mod = importlib.import_module("discord.ext.voice_recv")
            ver = getattr(mod, "__version__", "unknown")
            await ctx.send(f"voice_recv is importable, version {ver}")
        except Exception as exc:
            await ctx.send(f"voice_recv is not importable: {exc}\nEnsure the package is installed in the same Python interpreter Red is using, then try `[p]vreload` or restart the bot.`")
            return

        vc: discord.VoiceClient | None = ctx.voice_client
        if vc is None:
            await ctx.send("Bot is not connected to voice.")
            return

        listen = hasattr(vc, "listen")
        get_speaking = hasattr(vc, "get_speaking")
        await ctx.send(f"Voice client capabilities: listen={listen}, get_speaking={get_speaking}")

    @commands.command()
    async def vreload(self, ctx: commands.Context) -> None:
        """Attempt to import or reload the `voice_recv` package at runtime."""
        try:
            import importlib, sys
            if "voice_recv" in sys.modules:
                importlib.reload(sys.modules["voice_recv"])
            else:
                try:
                    importlib.import_module("voice_recv")
                except Exception:
                    importlib.import_module("discord.ext.voice_recv")
            # The module may be registered under discord.ext.voice_recv or voice_recv
            globals()["voice_recv"] = sys.modules.get("voice_recv") or sys.modules.get("discord.ext.voice_recv")
            await ctx.send("Successfully imported/reloaded voice_recv. If voice clients were already connected, you may need to reconnect them.")
        except Exception as exc:
            await ctx.send(f"Failed to import/reload voice_recv: {exc}\nInstall the package into the environment Red uses, then restart the bot if necessary.")
            self.logger.exception("vreload failed: %s", exc)

    @commands.command()
    @commands.is_owner()
    async def vdiag(self, ctx: commands.Context) -> None:
        """Diagnostic information about the bot's Python environment and `voice_recv` availability.

        Owner-only: prints the Python executable, version, site-packages locations,
        result of importlib.util.find_spec('voice_recv'), and `pip show` for the
        installed package (if available).
        """
        try:
            import importlib.util, site
            info = []
            info.append(("executable", sys.executable))
            info.append(("python_version", sys.version.replace('\n', ' ')))

            try:
                specs = importlib.util.find_spec("voice_recv")
                info.append(("voice_recv_spec", str(specs)))
            except Exception as e:
                info.append(("voice_recv_spec", f"error: {e}"))

            info.append(("voice_recv_in_sys_modules", str("voice_recv" in sys.modules)))

            try:
                site_pkgs = site.getsitepackages()
            except Exception:
                site_pkgs = []
            info.append(("site_packages", str(site_pkgs)))
            try:
                user_site = site.getusersitepackages()
            except Exception:
                user_site = "<unavailable>"
            info.append(("user_site_packages", str(user_site)))

            # Run pip show for more info
            pip_out = None
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "pip", "show", "discord-ext-voice-recv",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                out, err = await proc.communicate()
                if out:
                    pip_out = out.decode(errors="replace")
                elif err:
                    pip_out = f"pip show stderr: {err.decode(errors='replace')}"
                else:
                    pip_out = "pip show returned no output"
            except Exception as e:
                pip_out = f"pip show failed: {e}"

            # Build reply (truncate long sections)
            pip_snippet = (pip_out[:1500] + "...") if pip_out and len(pip_out) > 1500 else (pip_out or "<none>")

            lines = [f"{k}: {v}" for k, v in info]
            msg = "\n".join(lines)
            msg += "\n\npip show:\n" + pip_snippet
            # Send in code block if not too long
            if len(msg) < 1900:
                await ctx.send(f"```\n{msg}\n```")
            else:
                await ctx.send("Diagnostic output is large; sending top-level info and pip snippet.")
                await ctx.send(f"```\n{msg[:1900]}\n```")
        except Exception as exc:
            await ctx.send(f"vdiag failed: {exc}")
            self.logger.exception("vdiag failed: %s", exc)
    @commands.command()
    @commands.is_owner()
    async def vinstall(self, ctx: commands.Context, package: str = "discord-ext-voice-recv") -> None:
        """Install a runtime dependency into the bot's Python environment and try importing it.

        This command runs `python -m pip install <package>` using the Python
        interpreter the bot is running under. For safety it's restricted to the
        bot owner.
        """
        await ctx.send(f"Installing `{package}` into `{sys.executable}`...")
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await proc.communicate()
            code = proc.returncode
        except Exception as exc:
            await ctx.send(f"Failed to start installer: {exc}")
            return

        if code != 0:
            stderr = err.decode(errors="replace") if err else ""
            snippet = stderr[:1900]
            # Build content on one physical line so the source string is not split across lines
            content = f"Install failed (exit {code}). Stderr:\n```{snippet}```"
            await ctx.send(content)
            return

        await ctx.send(f"Install finished. Attempting to import `{package}`...")
        try:
            import importlib, sys as _sys
            if "voice_recv" in _sys.modules:
                importlib.reload(_sys.modules["voice_recv"])
                mod = _sys.modules["voice_recv"]
            else:
                try:
                    mod = importlib.import_module("voice_recv")
                except Exception:
                    mod = importlib.import_module("discord.ext.voice_recv")
            globals()["voice_recv"] = mod
            ver = getattr(mod, "__version__", "unknown")
            await ctx.send(f"Successfully installed and imported `voice_recv` (version {ver}).")
        except Exception as exc:
            await ctx.send(f"Install succeeded but import failed: {exc}\nYou may need to restart the bot.")
            self.logger.exception("Post-install import failed: %s", exc)




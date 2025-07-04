import discord
from redbot.core import commands
import socket
import asyncio
import re
import logging

class Ports(commands.Cog):
    """Cog for scanning and searching open ports on a given host."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger("redbot.cogs.Ports")
        self.rate_limit = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)

    @commands.Cog.listener()
    async def on_message(self, message):
        """React to bot mentions and process commands in messages."""
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message):
            await message.add_reaction('✅')
            await self.bot.process_commands(message)

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def scanports(self, ctx, host: str, start_port: int, end_port: int):
        """Scan a range of ports on a host and report which are open."""
        if not re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.[a-zA-Z]{2,})$", host):
            await ctx.send("Invalid host format.")
            return
        if start_port < 1 or end_port > 65535 or start_port > end_port:
            await ctx.send("Invalid port range.")
            return
        await ctx.typing()  # Show typing indicator
        open_ports = []
        tasks = []
        for port in range(start_port, end_port + 1):
            task = self.bot.loop.create_task(self.scan_port(ctx, host, port))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        for task in tasks:
            result = task.result()
            if isinstance(result, int):
                open_ports.append(result)
            elif result:
                await ctx.send(f'Error: {result}')
        if open_ports:
            services = []
            for port in open_ports:
                try:
                    service = socket.getservbyport(port)
                    services.append(f'{port}: {service}')
                except OSError:
                    services.append(f'{port}: Unknown')
            await ctx.send(f'Open ports on {host}:\n{", ".join(services)}')
        else:
            await ctx.send(f'No open ports found on {host}.')

    async def scan_port(self, ctx, host, port):
        """Attempt to connect to a port and return if it is open or an error message."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                sock.close()
                return port
        except socket.gaierror as e:
            return f'Error: Hostname {host} could not be resolved. {e}'
        except socket.error as e:
            return f'Error: Could not connect to server {host}. {e}'
        except asyncio.TimeoutError as e:
            return f'Error: Connection to {host} timed out. {e}'
        except Exception as e:  # Catch all exceptions
            return f'Error: {e}'
        finally:
            sock.close()

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def searchports(self, ctx, host: str):
        """Search for open ports on a host from 1 to 65535 and report which are open."""
        if not re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.[a-zA-Z]{2,})$", host):
            await ctx.send("Invalid host format.")
            return
        await ctx.typing()  # Show typing indicator
        open_ports = []
        tasks = []
        for port in range(1, 65536):
            task = self.bot.loop.create_task(self.scan_port(ctx, host, port))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        for task in tasks:
            result = task.result()
            if isinstance(result, int):
                open_ports.append(result)
            elif result:
                await ctx.send(f'Error: {result}')
        if open_ports:
            services = []
            for port in open_ports:
                try:
                    service = socket.getservbyport(port)
                    services.append(f'{port}: {service}')
                except OSError:
                    services.append(f'{port}: Unknown')
            await ctx.send(f'Open ports on {host}:\n{", ".join(services)}')
        else:
            await ctx.send(f'No open ports found on {host}.')


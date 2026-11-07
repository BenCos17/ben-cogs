"""Provide the legacy Red task module name during CI cog validation."""

import sys

import discord.ext.tasks as discord_tasks
import redbot.core

sys.modules.setdefault("redbot.core.tasks", discord_tasks)
redbot.core.tasks = discord_tasks

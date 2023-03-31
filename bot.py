# ==================================================================================================
# HamBot                            Created by William Yao                   Last updated 2023-03-31
# --------------------------------------------------------------------------------------------------
# HamBot is a server utility bot that allows friends to coordinate and schedule gaming activities.
# This is the main file to run HamBot on all connected servers.
# ==================================================================================================
import os
import discord

import dotenv
from discord.ext import commands, tasks

import poll


# ==================================================================================================
# INITIALIZE BOT
# ==================================================================================================
# Retrieve bot information from .env
dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
guild_ids = [int(guild_id) for guild_id in GUILD.split(",")]

# Create bot
intents = discord.Intents().all()  # Grant all permissions
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize server-specific bot data
poll_managers = {}


@bot.event
async def on_ready() -> None:
    """Print each of the bot's connected servers and initialize server-specific data.
    """
    print(f"{bot.user} is connected to the following guild(s):\n")
    for gid in guild_ids:
        # Print list of connected guilds
        print(f"{bot.get_guild(gid)} (id: {gid})")

        # Initialize data for this server
        poll_managers[gid] = poll.PollManager()


# ==================================================================================================
# EVENT HANDLERS
# ==================================================================================================
@bot.event
async def on_message(message) -> None:
    """Process incoming messages.
    """
    # Return early if bot is responding to itself
    if message.author == bot.user:
        return

    gid = message.guild.id

    # Manage polls
    await poll_managers[gid].create_poll(message)


@bot.event
async def on_reaction_add(reaction, reactor) -> None:
    """Process incoming reactions.
    """
    # Return early if bot is responding to itself
    if reactor == bot.user:
        return

    gid = reaction.message.guild.id

    # Manage polls
    await poll_managers[gid].update_poll(reaction, reactor)


# ==================================================================================================
# RUN BOT
# ==================================================================================================
bot.run(TOKEN)

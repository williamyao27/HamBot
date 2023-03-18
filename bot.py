import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from typing import Union


# Retrieve bot information from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
guild_ids = [int(guild_id) for guild_id in GUILD.split(",")]


# ==================================================================================================
# SETUP BOT
# ==================================================================================================
bot = commands.Bot(command_prefix="!")

# Bot constants
yes_emoji = "🟩"
wait_emoji = "🟨"
no_emoji = "🟥"
question_keywords = {"any", "?", "in the chat", "wanna", "want"}
val_keywords = {"val", "baler", "comper", "unrater", "5stack", "5 stack", "5man", "5 man", "fifth",
                "bal upper", "baller"}
player_threshold = 3

# Server-specific bot data
latest_poll = {}
latest_poll_caller = {}
yes_users = {}
wait_users = {}
no_users = {}


@bot.event
async def on_ready() -> None:
    """Print each of the bot's connected servers and initialize server-specific data.
    """
    print(f"{bot.user} is connected to the following guild(s):\n")
    for gid in guild_ids:
        # Print list of connected guilds
        print(f"{bot.get_guild(gid)} (id: {gid})")

        # Initialize data for this server
        latest_poll[gid] = None
        latest_poll_caller[gid] = None
        yes_users[gid] = []
        wait_users[gid] = []
        no_users[gid] = []


# ==================================================================================================
# BOT BEHAVIOR HELPERS
# ==================================================================================================
def detect_poll_request(contents) -> Union[str, None]:
    """Detect whether an invitation to play a game is contained in the contents string.
    Return string of the game's name.
    """
    contents = contents.lower()
    if any(keyword in contents for keyword in question_keywords):
        if any(keyword in contents for keyword in val_keywords):
            return "Valorant"

    return None


def track_poll(gid, poll_message, poll_caller) -> None:
    """Add the specified poll_message and poll_caller to the server-specific bot data.
    """
    latest_poll[gid] = poll_message
    latest_poll_caller[gid] = poll_caller


def add_to_poll_list(gid, user, avail) -> None:
    """Add the user to the poll list corresponding to avail. If the user is any other poll lists,
    they are removed from them.
    """
    # Remove user from all availability lists
    for lst in [yes_users[gid], wait_users[gid], no_users[gid]]:
        try:
            lst.remove(user)
        except ValueError:
            pass

    # Add user to the specified availability list
    if avail == "yes":
        yes_users[gid].append(user)
    elif avail == "wait":
        wait_users[gid].append(user)
    elif avail == "no":
        no_users[gid].append(user)


def stringify_poll_list(gid, avail) -> str:
    """Return a formatted string listing every user in the availability given by avail.
    """
    poll_list = None
    emoji = ""
    match avail:
        case "yes":
            poll_list = yes_users[gid]
            emoji = yes_emoji
        case "wait":
            poll_list = wait_users[gid]
            emoji = wait_emoji
        case "no":
            poll_list = no_users[gid]
            emoji = no_emoji

    if len(poll_list) == 0:
        return "*n/a*"
    else:
        str_so_far = ""
        for user in poll_list:
            str_so_far += emoji + "  " + f"{user.display_name}\n"
        return str_so_far


def clear_poll_lists(gid) -> None:
    """Clear all poll lists for this server.
    """
    for lst in [yes_users[gid], wait_users[gid], no_users[gid]]:
        lst.clear()


def check_redundant_reaction(gid, reactor) -> bool:
    """Check whether the reactor is already a yes on the poll.
    """
    return reactor in yes_users[gid]


def write_pings(gid) -> str:
    """Return a formatted string that pings every user that indicates yes for this poll.
    """
    if yes_users[gid] == set():
        return "*n/a*"
    else:
        str_so_far = ""
        for user in yes_users[gid]:
            str_so_far += user.mention + ", "
        return str_so_far[0:len(str_so_far) - 2]


# ==================================================================================================
# EVENT HANDLERS
# ==================================================================================================
@bot.event
async def on_message(message) -> None:
    """Send a notification to a channel when a server member requests to play Valorant in that
    channel.
    """
    channel = message.channel
    author = message.author
    gid = message.guild.id

    # Return early if bot is responding to itself
    if author == bot.user:
        return

    # Determine if message author is requesting to play Valorant
    if detect_poll_request(message.content):

        # Clear any previous poll lists
        clear_poll_lists(gid)

        # Mark availability of author as "yes" by default
        add_to_poll_list(gid, author, "yes")

        # Prepare embed to reply with
        poll_embed = discord.Embed(title=f"**{author.display_name}** wants to play Valorant!",
                                   url="https://github.com/williamyao27",
                                   description="React here to indicate availability.",
                                   color=0xFF5733)
        poll_embed.set_author(name=author.name, icon_url=author.avatar_url)
        poll_embed.set_thumbnail(url="https://seeklogo.com/images/V/valorant-logo-FAB2CA0E55-seeklogo.com.png")
        poll_embed.add_field(name="**Yes:**",
                             value=stringify_poll_list(gid, "yes"),
                             inline=True)
        poll_embed.add_field(name="**Wait:**",
                             value=stringify_poll_list(gid, "wait"),
                             inline=True)
        poll_embed.add_field(name="**No:**",
                             value=stringify_poll_list(gid, "no"),
                             inline=True)

        # Send embed as message, and save message
        response = await channel.send(embed=poll_embed)
        track_poll(gid, response, message.author)

        # React to own message with options
        await response.add_reaction(yes_emoji)
        await response.add_reaction(wait_emoji)
        await response.add_reaction(no_emoji)


@bot.event
async def on_reaction_add(reaction, reactor) -> None:
    """Edit the bot"s latest poll message if users interact with it by adding the proper
    reactions.
    """
    message = reaction.message
    channel = message.channel
    gid = message.guild.id
    redundant = check_redundant_reaction(gid, reactor)

    # Return early if bot is responding to itself
    if reactor == bot.user:
        return

    # Detect if the reaction was added to the bot"s latest poll
    if message.id == latest_poll[gid].id:

        # Update user lists based on user reaction
        if reaction.emoji == yes_emoji:
            add_to_poll_list(gid, reactor, "yes")

        elif reaction.emoji == wait_emoji:
            add_to_poll_list(gid, reactor, "wait")

        elif reaction.emoji == no_emoji:
            add_to_poll_list(gid, reactor, "no")

        # Clone original embed
        poll_embed_dict = message.embeds[0].to_dict()

        # Update clone
        for field in poll_embed_dict["fields"]:
            if field["name"] == "**Yes:**":
                field["value"] = stringify_poll_list(gid, "yes")

            if field["name"] == "**Wait:**":
                field["value"] = stringify_poll_list(gid, "wait")

            if field["name"] == "**No:**":
                field["value"] = stringify_poll_list(gid, "no")

        # Assign clone of embed to original poll message
        new_poll_embed = discord.Embed.from_dict(poll_embed_dict)
        await message.edit(embed=new_poll_embed)

        # Check if enough players are ready to play; only when a positive reaction is updated and
        # the reactor did not already vote yes
        if reaction.emoji == yes_emoji and len(yes_users[gid]) >= player_threshold and not redundant:
            # Prepare text and embed to ping with
            text = write_pings(gid)

            ping_embed = discord.Embed(title=str(len(yes_users[gid])) + " players are ready!",
                                       url="https://github.com/williamyao27",
                                       description="",
                                       color=0xFF5733)
            ping_embed.set_author(name=latest_poll_caller[gid].name,
                                  icon_url=latest_poll_caller[gid].avatar_url)

            # Send embed as message
            await channel.send(text, embed=ping_embed)

        # Remove reaction
        if reactor != bot.user:
            await reaction.remove(reactor)


# ==================================================================================================
# RUN BOT
# ==================================================================================================
bot.run(TOKEN)

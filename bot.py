# bot.py
import os
import discord
import random
from dotenv import load_dotenv


# 1
from discord.ext import commands
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')


# 2
bot = commands.Bot(command_prefix='!')


# ==================================================================================================
# SETUP FUNCTION
# ==================================================================================================
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


# ==================================================================================================
# GAME POLL FUNCTION
# ==================================================================================================
question_keywords = {'any', '?', 'in the chat', 'wanna', 'want'}
val_keywords = {'val', 'baler', 'comper', 'unrater', '5stack', '5 stack', '5man', '5 man', 'fifth',
                'bal upper', 'baller'}

# Variables related to the bot's latest poll
player_threshold = 3
latest_bot_response = None
latest_message_author = None
yes_users = set()
wait_users = set()
no_users = set()
users_list = [yes_users, wait_users, no_users]


def move_to_user_list(users, user) -> None:
    """Adds the user to users. If the user is any lists of users, they are removed from them.
    """
    # Empty all lists
    for user_set in users_list:
        if user in user_set:
            user_set.remove(user)

    users.add(user)


def write_user_list(users, emoji) -> str:
    """Returns a formatted string indicating the ready status of every user in users.
    """
    if users == set():
        return '*n/a*'
    else:
        str_so_far = ''
        for user in users:
            str_so_far += emoji + '  ' + f'{user.display_name}\n'
        return str_so_far


def reset_user_sets() -> None:
    """Empties users.
    """
    for user_set in users_list:
        user_set = set()


def write_ping_list(users) -> str:
    """Returns a formatted string that pings every user in users.
    """
    if users == set():
        return '*n/a*'
    else:
        str_so_far = ''
        for user in users:
            str_so_far += user.mention + ', '
        return str_so_far[0:len(str_so_far) - 2]


@bot.event
async def on_message(message) -> None:
    """Sends a notification to a channel when a server member requests to play Valorant in that
    channel.
    """
    channel = message.channel

    # Global variables to keep track of information related to the bot's latest poll
    global latest_bot_response
    global latest_message_author
    global yes_users
    global wait_users
    global no_users

    # Return early if bot is responding to itself
    if message.author == bot.user:
        return

    # Determine if message author is requesting to play Valorant
    if any(keyword in message.content.lower() for keyword in question_keywords) and\
            any(keyword in message.content.lower() for keyword in val_keywords):

        # Reset any previous polls
        reset_user_sets()

        # Add author to yes_users by default
        move_to_user_list(yes_users, message.author)

        # Prepare embed to reply with
        embed = discord.Embed(title=f'**{message.author.display_name}** wants to play Valorant!',
                              url='https://github.com/williamyao27',
                              description='React here to indicate availability.',
                              color=0xFF5733)
        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        embed.set_thumbnail(url='https://seeklogo.com/images/V/valorant-logo-FAB2CA0E55-seeklogo.com.png')
        embed.add_field(name='**Yes:**',
                        value=write_user_list(yes_users, '🟩'),
                        inline=True)
        embed.add_field(name='**Wait:**',
                        value=write_user_list(wait_users, '🟨'),
                        inline=True)
        embed.add_field(name='**No:**',
                        value=write_user_list(no_users, '🟥'),
                        inline=True)

        # Send embed as message, and save message
        response = await channel.send(embed=embed)
        latest_bot_response = response
        latest_message_author = message.author

        # React to own message with options
        await response.add_reaction('🟩')
        await response.add_reaction('🟨')
        await response.add_reaction('🟥')

@bot.event
async def on_reaction_add(reaction, reactor) -> None:
    """Edits the bot's latest poll message if users interact with it by adding the proper
    reactions.
    """
    message = reaction.message
    channel = message.channel
    redundant = reactor in yes_users or reactor in wait_users

    # Return early if bot is responding to itself
    if reactor == bot.user:
        return

    # Detect if the reaction was added to the bot's latest poll
    if message.id == latest_bot_response.id:

        # Update user lists based on user reaction
        if reaction.emoji == '🟩':
            move_to_user_list(yes_users, reactor)

        elif reaction.emoji == '🟨':
            move_to_user_list(wait_users, reactor)

        elif reaction.emoji == '🟥':
            move_to_user_list(no_users, reactor)

        # Clone original embed
        embed_dict = message.embeds[0].to_dict()

        # Update clone
        for field in embed_dict['fields']:
            if field['name'] == '**Yes:**':
                field['value'] = write_user_list(yes_users, '🟩')

            if field['name'] == '**Wait:**':
                field['value'] = write_user_list(wait_users, '🟨')

            if field['name'] == '**No:**':
                field['value'] = write_user_list(no_users, '🟥')

        # Assign clone of embed to original poll message
        new_embed = discord.Embed.from_dict(embed_dict)
        await message.edit(embed=new_embed)

        # Check if enough players are ready to play; only when a positive reaction is updated and
        # the reactor did not already vote yes
        if len(yes_users) >= player_threshold and not redundant and (reaction.emoji == '🟩' or reaction.emoji == '🟨'):
            # Prepare text and embed to ping with
            text = write_ping_list(yes_users)

            embed = discord.Embed(title=str(len(yes_users)) + ' players are ready!',
                                  url='https://github.com/williamyao27',
                                  description='',
                                  color=0xFF5733)
            embed.set_author(name=latest_message_author.name,
                             icon_url=latest_message_author.avatar_url)

            # Send embed as message
            await channel.send(text, embed=embed)

        # Remove reaction
        if reactor != bot.user:
            await reaction.remove(reactor)


bot.run(TOKEN)

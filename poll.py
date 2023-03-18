# ==================================================================================================
# Contains all the behaviors for the bot to create and manage polls in a given server.
# ==================================================================================================
from typing import Union
import discord

# Constants
YES_EMOJI = "🟩"
WAIT_EMOJI = "🟨"
NO_EMOJI = "🟥"
QUESTION_KEYWORDS = {"any", "?", "in the chat", "wanna", "want"}
VAL_KEYWORDS = {"val", "baler", "comper", "unrater", "5stack", "5 stack", "5man", "5 man", "fifth",
                "bal upper", "baller"}
PLAYER_THRESHOLD = 3


class PollManager:
    """Creates and manages game-related polls for a single server.
    """
    def __init__(self):
        """Initialize the PollManager for this server.
        """
        self.__latest_poll = None
        self.__latest_poll_caller = None
        self.__poll_lists = {"yes": [], "wait": [], "no": []}

    def __detect_poll_request(self, content) -> Union[str, None]:
        """Detect whether an invitation to play a game is contained in the content string.
        Return string of the game's name.
        """
        content = content.lower()
        if any(keyword in content for keyword in QUESTION_KEYWORDS):
            if any(keyword in content for keyword in VAL_KEYWORDS):
                return "Valorant"

        return None

    def __track_poll(self, poll_message, poll_caller) -> None:
        """Add the specified poll_message and poll_caller to the server-specific bot data.
        """
        self.__latest_poll = poll_message
        self.__latest_poll_caller = poll_caller

    def __add_to_poll_list(self, user, avail) -> None:
        """Add the user to the poll list corresponding to avail. If the user is any other poll lists,
        they are removed from them.
        """
        # Remove user from all availability lists
        for lst in self.__poll_lists.values():
            try:
                lst.remove(user)
            except ValueError:
                pass

        # Add user to the specified availability list
        self.__poll_lists[avail].append(user)

    def __stringify_poll_list(self, avail) -> str:
        """Return a formatted string listing every user in the availability list given by avail.
        """
        lst = self.__poll_lists[avail]
        emoji = ""
        match avail:
            case "yes":
                emoji = YES_EMOJI
            case "wait":
                emoji = WAIT_EMOJI
            case "no":
                emoji = NO_EMOJI

        if len(lst) == 0:
            return "*n/a*"
        else:
            str_so_far = ""
            for user in lst:
                str_so_far += emoji + "  " + f"{user.display_name}\n"
            return str_so_far

    def __clear_poll_lists(self) -> None:
        """Clear all poll lists for this server.
        """
        for lst in self.__poll_lists.values():
            lst.clear()

    def __check_redundant_reaction(self, reactor, avail) -> bool:
        """Check whether the reactor is already in the given availability list.
        """
        return reactor in self.__poll_lists[avail]

    def __write_pings(self, avail) -> str:
        """Return a formatted string that pings every user on the given availability list.
        """
        lst = self.__poll_lists[avail]
        if len(lst) == 0:
            return "*n/a*"
        else:
            str_so_far = ""
            for user in lst:
                str_so_far += user.mention + ", "
            return str_so_far[0:len(str_so_far) - 2]

    async def create_poll(self, message) -> None:
        """Create and send a poll notification to the given channel when a server member requests to
         play Valorant in that channel.
        """
        channel = message.channel
        author = message.author

        # Determine if message author is requesting to play Valorant
        if self.__detect_poll_request(message.content):
            # Clear any previous poll lists
            self.__clear_poll_lists()

            # Mark availability of author as "yes" by default
            self.__add_to_poll_list(author, "yes")

            # Prepare embed to reply with
            poll_embed = discord.Embed(title=f"**{author.display_name}** wants to play Valorant!",
                                       url="https://github.com/williamyao27",
                                       description="React here to indicate availability.",
                                       color=0xFF5733)
            poll_embed.set_author(name=author.name, icon_url=author.avatar_url)
            poll_embed.set_thumbnail(
                url="https://seeklogo.com/images/V/valorant-logo-FAB2CA0E55-seeklogo.com.png")
            poll_embed.add_field(name="**Yes:**",
                                 value=self.__stringify_poll_list("yes"),
                                 inline=True)
            poll_embed.add_field(name="**Wait:**",
                                 value=self.__stringify_poll_list("wait"),
                                 inline=True)
            poll_embed.add_field(name="**No:**",
                                 value=self.__stringify_poll_list("no"),
                                 inline=True)

            # Send embed as message, and save message
            response = await channel.send(embed=poll_embed)
            self.__track_poll(response, author)

            # React to own message with options
            await response.add_reaction(YES_EMOJI)
            await response.add_reaction(WAIT_EMOJI)
            await response.add_reaction(NO_EMOJI)

    async def update_poll(self, reaction, reactor) -> None:
        """Edit the bot"s latest poll message if users interact with it by adding the proper
        reactions.
        """
        message = reaction.message
        channel = message.channel

        # Determine whether the user had already reacted yes to the poll
        redundant = self.__check_redundant_reaction(reactor, "yes")

        # Detect if the reaction was added to the bot's latest poll
        if message.id == self.__latest_poll.id:

            # Update user lists based on user reaction
            if reaction.emoji == YES_EMOJI:
                self.__add_to_poll_list(reactor, "yes")

            elif reaction.emoji == WAIT_EMOJI:
                self.__add_to_poll_list(reactor, "wait")

            elif reaction.emoji == NO_EMOJI:
                self.__add_to_poll_list(reactor, "no")

            # Clone original embed
            poll_embed_dict = message.embeds[0].to_dict()

            # Update clone
            for field in poll_embed_dict["fields"]:
                if field["name"] == "**Yes:**":
                    field["value"] = self.__stringify_poll_list("yes")

                if field["name"] == "**Wait:**":
                    field["value"] = self.__stringify_poll_list("wait")

                if field["name"] == "**No:**":
                    field["value"] = self.__stringify_poll_list("no")

            # Assign clone of embed to original poll message
            new_poll_embed = discord.Embed.from_dict(poll_embed_dict)
            await message.edit(embed=new_poll_embed)

            # Check if enough players are ready to play; only when a new yes reaction is added
            yes_list = self.__poll_lists["yes"]
            if reaction.emoji == YES_EMOJI and len(yes_list) >= PLAYER_THRESHOLD and not redundant:
                # Prepare text and embed to ping with
                text = self.__write_pings("yes")

                ping_embed = discord.Embed(title=str(len(yes_list)) + " players are ready!",
                                           url="https://github.com/williamyao27",
                                           description="",
                                           color=0xFF5733)
                ping_embed.set_author(name=self.__latest_poll_caller.name,
                                      icon_url=self.__latest_poll_caller.avatar_url)

                # Send embed as message
                await channel.send(text, embed=ping_embed)

            # Remove reaction
            await reaction.remove(reactor)

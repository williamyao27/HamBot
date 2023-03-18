# ==================================================================================================
# Contains all the behaviors for the bot to create message-based minigames in a server.
# ==================================================================================================
import discord
from discord.ext import tasks

# Constants


class PlantManager:
    """Creates and manages the server plant.
    """
    def __init__(self):
        """Initialize the PlantManager for this server.
        """
        self.__name = "Plant"
        self.__hydration = 100.
        self.__happiness = 100.
        self.__alive = True
        self.__death_cause = None
        self.tick.start()

    def __mood(self) -> str:
        """Return a string describing this plant's mood based on its happiness level.
        """
        if self.__happiness <= 0:
            return "Depressed"
        elif 0 < self.__happiness <= 20:
            return "Sad"
        elif 20 < self.__happiness <= 40:
            return "Wilting"
        elif 40 < self.__happiness <= 60:
            return "Mediocre"
        elif 60 < self.__happiness <= 80:
            return "Happy"
        elif 80 < self.__happiness <= 100:
            return "Joyous"

    async def __summary(self, ctx) -> None:
        """Send summary for this server's plant.
        """
        if self.__alive:
            # Summary of stats
            await ctx.send(":potted_plant:\n")
            await ctx.send(f"*{self.__name}*\n"
                           f"**Hydration:** {self.__hydration}%\n"
                           f"**Happiness:** {self.__happiness}% ({self.__mood()})")
        else:
            # Death overview
            await ctx.send(":skull:\n")
            await ctx.send(f"*{self.__name}*\n"
                           f"**Plant died due to {self.__death_cause}**.")

    async def __set_name(self, ctx, *args) -> None:
        """Set name for this server's plant and send notification.
        """
        if len(args) > 1:
            old_name = self.__name
            self.__name = " ".join(args[1:])  # Combine all remaining arguments into name
            await ctx.send(f"{old_name} renamed to {self.__name}.")
        else:
            # Incorrect usage
            await ctx.send("`!plant name <name>`")

    async def __water(self, ctx) -> None:
        """Increment hydration for this server's plant and send notification.
        """
        self.__hydration += 10.
        await ctx.send(f"Thanks for watering the plant! Its hydration is {self.__hydration}%.")

    async def __pet(self, ctx) -> None:
        """Increment happiness for this server's plant and send notification.
        """
        self.__happiness += 10.
        self.__happiness = min(self.__happiness, 100.)
        await ctx.send(f"Thanks for petting the plant! Its happiness is {self.__happiness}%.")

    async def process_cmd(self, ctx, *args) -> None:
        """Process any call to the !plant command for this server.
        """
        # If no arguments, then show stats for the plant
        if len(args) == 0:
            await self.__summary(ctx)

        # Respawn the plant
        elif args[0] == "respawn":
            pass

        # Except for respawning, no other commands are permitted with a dead plant
        elif not self.__alive:
            await ctx.send(f"You cannot interact with {self.__name} because it died.")

        # Otherwise, process command intent
        else:
            match args[0]:
                case "water":
                    await self.__water(ctx)
                case "pet":
                    await self.__pet(ctx)
                case "name":
                    await self.__set_name(ctx, *args)
                case _:
                    # Unknown command, react with ?
                    await ctx.message.add_reaction("❓")

    @tasks.loop(seconds=20)
    async def tick(self) -> None:
        """Re-evaluate plant stats for this new time period.
        """
        if self.__alive:
            # Lose hydration (100% per 15,000 seconds = 5.5 hrs)
            self.__hydration = round(self.__hydration - 0.05, 2)

            # Kill plant if over or underhydrated
            if self.__hydration > 200:
                self.__death_cause = "overwatering"
                self.__alive = False
            if self.__hydration < 0:
                self.__death_cause = "underwatering"
                self.__alive = False

            # Lose happiness (exponential decay)
            self.__happiness = round(self.__happiness * 0.995, 2)

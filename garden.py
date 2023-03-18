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
        self.__hydration = 100.
        self.__happiness = 50.
        self.__alive = True
        self.__death_cause = None
        self.tick.start()

    def __water(self) -> float:
        """Increment hydration for this server's plant. Return the hydration level after watering.
        """
        self.__hydration += 10.
        return self.__hydration

    def __pet(self) -> float:
        """Increment happiness for this server's plant. Return the happiness level after petting.
        """
        self.__happiness += 10.
        self.__happiness = min(self.__happiness, 100.)
        return self.__happiness

    def __mood(self) -> str:
        """Return a string describing this plant's mood based on its happiness level.
        """
        if self.__happiness <= 0:
            return "Gone"
        elif 0 < self.__happiness <= 20:
            return "Depressed"
        elif 20 < self.__happiness <= 40:
            return "Sad"
        elif 40 < self.__happiness <= 60:
            return "Mediocre"
        elif 60 < self.__happiness <= 80:
            return "Happy"
        elif 80 < self.__happiness <= 100:
            return "Joyous"

    async def process_cmd(self, ctx, *args) -> None:
        """Process any call to the !plant command for this server.
        """
        # If no arguments, then show stats for the plant
        if len(args) == 0:
            if self.__alive:
                await ctx.send(":potted_plant:\n\n"
                               f"**Hydration:** {self.__hydration}%\n"
                               f"**Happiness:** {self.__happiness}% ({self.__mood()})")
            else:
                await ctx.send(":skull:\n\n"
                               f"**Plant died due to {self.__death_cause}**.")

        elif not self.__alive:
            await ctx.send("You cannot interact with the plant because it died.")

        # Otherwise, process command intent
        else:
            match args[0]:
                case "water":
                    await ctx.send(f"Thanks for watering the plant! "
                                   f"Its hydration is {self.__water()}%.")
                case "pet":
                    await ctx.send(f"Thanks for petting the plant! "
                                   f"Its happiness is {self.__pet()}%.")
                case _:
                    # unknown command, react with ?
                    await ctx.message.add_reaction("❓")

    @tasks.loop(seconds=10)
    async def tick(self) -> None:
        """Re-evaluate plant stats for this new time period.
        """
        if self.__alive:
            # Lose hydration (100% per 10,000 seconds = 166 mins)
            self.__hydration = round(self.__hydration - 0.1, 1)

            # Kill plant if over or underhydrated
            if self.__hydration > 110:
                self.__death_cause = "overwatering"
                self.__alive = False
            if self.__hydration < 0:
                self.__death_cause = "underwatering"
                self.__alive = False

            # Lose happiness (exponential decay)
            self.__happiness = round(self.__happiness * 0.99, 1)

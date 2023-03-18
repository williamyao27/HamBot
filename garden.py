# ==================================================================================================
# Contains all the behaviors for the bot to create message-based minigames in a server.
# ==================================================================================================
from discord.ext import tasks
import pickle

# Constants


class PlantManager:
    """Creates and manages the server plant.
    """
    def __init__(self, gid):
        """Initialize the PlantManager for this server.
        """
        self.__gid = gid  # Store gid for this manager so it can be pickled to the proper file

        # Find and load this server's plant information from pickle
        try:
            self.__load()
        except FileNotFoundError:
            # If none found, then initialize a new plant
            self.__reset_plant()

        self.tick.start()

    def __reset_plant(self) -> None:
        """Initialize the stats of the plant for this PlantManager.
        """
        self.__name = "Plant"
        self.__hydration = 100.
        self.__happiness = 100.
        self.__alive = True
        self.__death_cause = None

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

    async def __respawn(self, ctx) -> None:
        """Respawn this server's plant.
        """
        if self.__alive:
            await ctx.send(f"Cannot respawn the plant because {self.__name} is still alive.")
        else:
            self.__reset_plant()
            await ctx.send("Respawned the plant.")

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
            await self.__respawn(ctx)

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

    def __dump(self) -> None:
        """Write the relevant attributes of this server's plant as a dictionary into a pickle file.
        """
        attributes = {
            "name": self.__name,
            "hydration": self.__hydration,
            "happiness": self.__happiness,
            "alive": self.__alive,
            "death_cause": self.__death_cause,
        }

        with open(f"plant_managers/{self.__gid}.pickle", "wb") as fp:
            pickle.dump(attributes, fp)

    def __load(self) -> None:
        """Set attributes of this server's plant with the dictionary from its pickle file.
        """
        with open(f"plant_managers/{self.__gid}.pickle", "rb") as fp:
            attributes = pickle.load(fp)

        self.__name = attributes["name"]
        self.__hydration = attributes["hydration"]
        self.__happiness = attributes["happiness"]
        self.__alive = attributes["alive"]
        self.__death_cause = attributes["death_cause"]

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

        # Save plant information
        self.__dump()

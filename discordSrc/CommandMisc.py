__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

from typing import List
import discord

from .ICommand import ICommand
from .IMiscCommand import IMiscCommand
from .MiscCommandPet import MiscCommandPet

from config.ClassLogger import ClassLogger, LogLevel

class CommandMisc(ICommand):
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        super().__init__()

        self.command = discord.app_commands.Command(
            name="misc",
            description="Run a miscellaneous command.",
            callback=self.runMisc,
        )

        self.miscCommands: List[IMiscCommand] = [
            MiscCommandPet(),
        ]

    def setupCommands(self, tree:discord.app_commands.CommandTree):
        CommandMisc.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Initializing the misc command.")
        tree.add_command(self.command)

    @discord.app_commands.describe(command="Name of the command to run")
    async def runMisc(self, interaction: discord.Interaction, command: str):
        found = False
        for cmd in self.miscCommands:
            if command == cmd.getCommandName():
                await cmd.runCommand(interaction)
                found = True
                break

        if not found:
            await interaction.response.send_message(f"There is no command named \"{command}\"", ephemeral=True)


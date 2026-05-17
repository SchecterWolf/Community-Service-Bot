__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "schecterwolfe@gmail.com"

import discord

from .ICommand import ICommand
from .MinecraftStat import MinecraftStat, EC2State

from config.ClassLogger import ClassLogger, LogLevel

from typing import List

class CommandMinecraft(ICommand):
    __LOGGING = ClassLogger(__name__)

    def __init__(self):
        super().__init__()

        self.commands: List[discord.app_commands.Command] = [
            discord.app_commands.Command(
                name="start_minecraft",
                description="Start the community minecraft server",
                callback=self.startMC
            ),
            discord.app_commands.Command(
                name="minecraft_status",
                description="Check the state of the minecraft server",
                callback=self.statMC
            )
        ]

    def setupCommands(self, tree: discord.app_commands.CommandTree):
        CommandMinecraft.__LOGGING.log(LogLevel.LEVEL_DEBUG, f"Initializing minecraft commands.")
        for cmd in self.commands:
            tree.add_command(cmd)

    async def startMC(self, interaction: discord.Interaction):
        CommandMinecraft.__LOGGING.log(LogLevel.LEVEL_DEBUG, f"Start minecraft server called by user {interaction.user.name}")
        await interaction.response.defer(thinking=True)

        minecraft = MinecraftStat(interaction.guild_id or 0)

        # Check if the server is already running
        status = minecraft.get_status()
        if status == EC2State.PENDING or status == EC2State.RUNNING:
            await interaction.followup.send("The community minecraft server is already running.")
            return

        minecraft.start()
        await interaction.followup.send("Starting up the community minecraft server, please wait a few minutes...")

    async def statMC(self, interaction: discord.Interaction):
        CommandMinecraft.__LOGGING.log(LogLevel.LEVEL_DEBUG, f"Status minecraft server called by user {interaction.user.name}")
        await interaction.response.defer(thinking=True)

        minecraft = MinecraftStat(interaction.guild_id or 0)
        status = str(minecraft.get_status().value.upper())
        await interaction.followup.send(f"Minecraft server status: {status}")


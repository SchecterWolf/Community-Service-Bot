__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
import core.CommsServiceFactory as CommsServiceFactory

from .CommsTypeSelect import CommsTypeSelect
from .Decorators import require_jailmod
from .DiscordBailiff import DiscordBailiff

from config.ClassLogger import ClassLogger, LogLevel
from core.CommType import CommType
from core.Community import Community
from core.InmateData import InmateData

from typing import cast

class CommsPropertiesModal(discord.ui.Modal):
    __LOGGER = ClassLogger(__name__)
    __TITLE = "Community Service Properties"

    subtitle = discord.ui.TextDisplay(content="")

    commsCategoryDropdown = discord.ui.Label(
        text="Punishment Type",
        component=CommsTypeSelect()
    )

    numRoundsInput = discord.ui.Label(
        text="Cycle Count",
        component=discord.ui.TextInput()
    )

    reasonInput = discord.ui.Label(
        text="Reason",
        component=discord.ui.TextInput(style=discord.TextStyle.paragraph, placeholder="(optional)")
    )

    def __init__(self, user: discord.Member, bailiff: DiscordBailiff):
        self.subtitle.content = f"Sending user {user.display_name} to community service!"
        super().__init__(title=CommsPropertiesModal.__TITLE)

        self.user = user
        self.bailiff = bailiff

    @require_jailmod
    async def on_submit(self, interaction: discord.Interaction):
        CommsPropertiesModal.__LOGGER.log(LogLevel.LEVEL_INFO, f"Mod \"{interaction.user.display_name}\" is sending \"{self.user.display_name}\" to community service!")

        # Error check
        if not int(cast(discord.ui.TextInput, self.numRoundsInput.component).value):
            await interaction.response.send_message("Invalid value for rounds. Must be an integer greater than 0.", ephemeral=True)

        await interaction.response.defer(thinking=True, ephemeral=True)

        # Pull the input data from the modal
        commsType: CommType = cast(CommsTypeSelect, self.commsCategoryDropdown.component).getType()
        numRounds: int = int(cast(discord.ui.TextInput, self.numRoundsInput.component).value)
        reason = cast(discord.ui.TextInput, self.reasonInput.component).value

        # Create the inmate
        inmate = InmateData(
            id = 0,
            serverid = interaction.guild_id or 0,
            userid = self.user.id,
            roles = {role.id for role in self.user.roles},
            mode = commsType,
            rounds = numRounds,
        )

        # Incarserate user
        serviceGame = None
        res = await self.bailiff.commitInmate(inmate, self.user.display_name)

        # Start the community service game
        if not res.result:
            CommsPropertiesModal.__LOGGER.log(LogLevel.LEVEL_DEBUG, res.errorStr)
            await interaction.followup.send(res.errorStr)
        else:
            reason = f"Greetings {self.user.mention}! You have been given community service" \
                + f" for the following reason: {reason}" if reason else "!"
            serviceGame = CommsServiceFactory.createServiceGame(self.user.display_name, inmate, self.bailiff, reason)
            res = await serviceGame.start()

        # Add the game to the community if successfull, otherwise release the user
        if serviceGame and res.result:
            Community().addServiceGame(serviceGame)
        else:
            await self.bailiff.speakToInmate(f"We had a problem setting up the community service. User will be released!")
            await self.bailiff.releaseInmate(inmate, self.user.display_name)

        if res.result:
            await interaction.followup.send(f"User \"{self.user.display_name}\" has been sent to community service!")


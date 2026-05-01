__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import asyncio
import discord
import time

from dataclasses import dataclass
from typing import Dict, Optional, cast

from .IMiscCommand import IMiscCommand

from config.ClassLogger import ClassLogger, LogLevel

@dataclass
class ActionUser:
    name: str = ""
    userID: int = 0
    numActions: int = 0

@dataclass
class ActionVerbElement:
    embed: discord.Embed
    button: discord.ui.Button
    message: discord.Message
    verb: str
    created: float
    name: str
    element: Dict[int, ActionUser]

class MiscCommandPet(discord.ui.Modal, IMiscCommand):
    __LOGGER = ClassLogger(__name__)
    __TITLE = "Give Pets Command"
    __MAX_DISPLAY_USERS = 10
    __ACTIVE_TIME_SEC = 1200 # 20 minutes
    __POLLING_SEC = 30

    subTitle = discord.ui.TextDisplay(content="Give someone pets!")

    petUser = discord.ui.Label(
        text="User to give pets too",
        component=discord.ui.UserSelect(min_values=1, max_values=1)
    )

    actionVerb = discord.ui.Label(
        text="Action verb (pets, hugs, etc)",
        component=discord.ui.TextInput(default="pets", required=False)
    )

    def __init__(self):
        super().__init__(title=MiscCommandPet.__TITLE)
        self.ongoing: Dict[int, ActionVerbElement] = dict()
        self.expiryTask: Optional[asyncio.Task] = None

    def getCommandName(self) -> str:
        return "givepets"

    async def runCommand(self, interaction: discord.Interaction):
        self.__startExpiryTask()
        await interaction.response.send_modal(self)

    async def on_submit(self, interaction: discord.Interaction):
        MiscCommandPet.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"User {interaction.user.name} ran the pets command.")
        userValues = cast(discord.ui.UserSelect, self.petUser.component).values
        verb = cast(discord.ui.TextInput, self.actionVerb.component).value

        if not userValues:
            await interaction.response.send_message("You must select a server member", ephemeral=True)
            return
        elif userValues[0].id in self.ongoing:
            await interaction.response.send_message(f"{userValues[0].name} is already getting {verb}.", ephemeral=True)
            return
        elif not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("You can only use this command with text channels.")
            return
        elif not verb or not verb.strip():
            await interaction.response.send_message("You must specify an action verb.", ephemeral=True)
            return

        # Create the embed
        user = userValues[0]
        embed = discord.Embed(title=f"Give {verb} to {user.display_name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=user.display_avatar.url)

        # Create the action button
        button = discord.ui.Button(custom_id=str(user.id), label=f"Click to give {verb}!", style=discord.ButtonStyle.primary)
        button.callback = self.actionClicked
        button.interaction_check = self.interactionCheck
        view = discord.ui.View()
        view.add_item(button)

        # Send the embed
        message = await interaction.channel.send(embed=embed, view=view)
        self.ongoing[user.id] = ActionVerbElement(embed=embed, button=button, message=message,
                                                  verb=verb, created=time.time(), name=user.name, element=dict())
        await interaction.response.defer()

        MiscCommandPet.__LOGGER.log(LogLevel.LEVEL_INFO, f"Member {user.display_name} was set to receive pets.")

    async def interactionCheck(self, interaction: discord.Interaction) -> bool:
        userID = int(interaction.custom_id or "")
        actionElement = self.ongoing.get(userID, None)

        if not actionElement or time.time() - actionElement.created >= MiscCommandPet.__ACTIVE_TIME_SEC:
            await interaction.response.send_message("Activity has ended.", ephemeral=True)
            return False
        else:
            return True

    async def actionClicked(self, interaction: discord.Interaction):
        userID = int(interaction.custom_id or "")
        if userID not in self.ongoing:
            await interaction.response.send_message("Activity has ended.", ephemeral=True)
            return

        # Ack
        await interaction.response.defer()

        # Increment action number
        actionElement = self.ongoing[userID]
        actionInfo: ActionUser = actionElement.element.setdefault(interaction.user.id, ActionUser(name=interaction.user.display_name, userID=interaction.user.id))
        actionInfo.numActions += 1

        # Update the embed description
        allActionUsers = sorted(actionElement.element.values(), key=lambda data: data.numActions, reverse=True)[:MiscCommandPet.__MAX_DISPLAY_USERS]
        description = ""
        for usr in allActionUsers:
            modifier = ""
            if usr.userID == actionInfo.userID:
                modifier = "**"
            description += f"{modifier}{usr.name} gave {usr.numActions} {actionElement.verb}{modifier}\n"

        # Update the embed
        actionElement.embed.description = description
        actionElement.embed.set_footer(text=f"{actionInfo.name} gave {actionElement.verb}")
        if not await self.__updateActivity(actionElement):
            self.ongoing.pop(userID, None)

    def __startExpiryTask(self):
        if self.expiryTask is None or self.expiryTask.done():
            self.expiryTask = asyncio.create_task(self.__expiryLoop())

    async def __expiryLoop(self):
        while True:
            try:
                now = time.time()
                expiredUsers: list[int] = []

                for userID, actionElement in list(self.ongoing.items()):
                    if now - actionElement.created < MiscCommandPet.__ACTIVE_TIME_SEC:
                        continue

                    expiredUsers.append(userID)

                    # Rebuild the view with the disabled button
                    await self.__updateActivity(actionElement, False)

                for userID in expiredUsers:
                    self.ongoing.pop(userID, None)
                    MiscCommandPet.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Expired petting action removed for userID {userID}.")

                await asyncio.sleep(MiscCommandPet.__POLLING_SEC)

            except Exception as ex:
                MiscCommandPet.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Expiry loop error: {ex}")
                await asyncio.sleep(MiscCommandPet.__POLLING_SEC)

    async def __updateActivity(self, actionElement: ActionVerbElement, addButton = True) -> bool:
        view = discord.ui.View()
        if addButton:
            view.add_item(actionElement.button)

        try:
            await actionElement.message.edit(embed=actionElement.embed, view=view)
        except discord.NotFound:
            MiscCommandPet.__LOGGER.log(LogLevel.LEVEL_WARN, f"Could not update expired action message for {actionElement.name}: message no longer exists.")
            return False
        except discord.HTTPException as ex:
            MiscCommandPet.__LOGGER.log(LogLevel.LEVEL_WARN, f"Failed to update expired action message for {actionElement.name}: {ex}")
            return False

        return True


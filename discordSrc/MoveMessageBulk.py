__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord

from .BulkMoveConfirmView import BulkMoveConfirmView
from .Decorators import verifyIsJailmod
from .ICommand import ICommand
from .MoveMessage import MoveMessage
from .MoveMessageModal import MoveMessageModal

from config.ClassLogger import ClassLogger, LogLevel

from typing import List

class MoveMessageBulk(discord.app_commands.ContextMenu, ICommand):
    __LOGGER = ClassLogger(__name__)
    __MAX_MOVE_LIMIT = 200

    def __init__(self):
        super().__init__(name="Bulk Move Message", callback=self.callback, type=discord.AppCommandType.message)

    def setupCommands(self, tree: discord.app_commands.CommandTree):
        MoveMessageBulk.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Initializing the move message bulk command.")
        tree.add_command(self)

    async def callback(self, interaction: discord.Interaction, message: discord.Message):
        MoveMessageBulk.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Bulk move message command invoked by user \"{interaction.user.display_name}\".")
        if not await verifyIsJailmod(interaction):
            return

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("This command can only be used in text channels.", ephemeral=True)
            return

        try:
            # Prompt for the transfer channel
            modal = MoveMessageModal()
            await interaction.response.send_modal(modal)
            timedOut = await modal.wait()
            if timedOut:
                await interaction.followup.send("Timed out waiting for channel selection.", ephemeral=True)
                return

            # Retrieve the transfer channel
            selected = modal.selectedChannel
            if selected is None:
                await interaction.followup.send("No channel selected.", ephemeral=True)
                return

            # Gather bulk messages
            messages: List[discord.Message] = []
            count = 0
            async for msg in channel.history(limit=None):
                messages.append(msg)
                count += 1

                if msg.id == message.id:
                    break

                if count >= MoveMessageBulk.__MAX_MOVE_LIMIT:
                    await interaction.followup.send(f"Wipe guard, you cannot move more than {MoveMessageBulk.__MAX_MOVE_LIMIT} message.", ephemeral=True)
                    return
            messages.reverse()

            # Confirm move messages
            confirmButtons = BulkMoveConfirmView()
            await interaction.followup.send(f"You are about to move {len(messages)} messages to {selected.mention}. Are you sure?",
                                                          view=confirmButtons, ephemeral=True)
            timedOut = await confirmButtons.wait()

            # Move bulk messages
            if timedOut or not confirmButtons.confirmed:
                MoveMessageBulk.__LOGGER.log(LogLevel.LEVEL_INFO, "Bulk move message aborted")
            else:
                mm = MoveMessage()
                for msg in messages:
                    await mm.moveSingleMessage(interaction, selected.id, msg, False)

        except TimeoutError:
            await interaction.followup.send("Timed out waiting for channel mention.", ephemeral=True)


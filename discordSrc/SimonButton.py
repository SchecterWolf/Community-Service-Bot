__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from typing import Awaitable, Callable

class SimonButton(discord.ui.Button):
    def __init__(self, color: str, emoji: str, userID: int, gameCallback: Callable[[str], Awaitable[None]]):
        super().__init__(label=color.capitalize(), emoji=emoji, style=discord.ButtonStyle.primary)
        self.userID = userID
        self.gameCallback = gameCallback

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.userID:
            await interaction.response.send_message("This game isn't for you!", ephemeral=True)
            return
        await interaction.response.defer()
        await self.gameCallback(self.label or "")

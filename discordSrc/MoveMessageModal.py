__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord
from typing import cast

class MoveMessageModal(discord.ui.Modal):
    __TIMEOUT_SEC = 60

    targetChannel = discord.ui.Label(
        text="Channel to move message to",
        component=discord.ui.ChannelSelect(min_values=1, max_values=1)
    )

    def __init__(self):
        super().__init__(title="Move Message", timeout=MoveMessageModal.__TIMEOUT_SEC)

        self.selectedChannel = None

    async def on_submit(self, interaction: discord.Interaction):
        values = cast(discord.ui.ChannelSelect, self.targetChannel.component).values
        self.selectedChannel = values[0] if values else None
        await interaction.response.defer(ephemeral=True)


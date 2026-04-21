__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord

class BulkMoveConfirmView(discord.ui.View):
    def __init__(self, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.confirmed: bool = False

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirmButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        await interaction.response.edit_message(content="Bulk move confirmed.", view=discord.ui.View())
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancelButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        await interaction.response.edit_message(content="Bulk move cancelled.", view=discord.ui.View())
        self.stop()


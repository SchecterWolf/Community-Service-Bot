__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .SimonButton import SimonButton

from core.IFace import IFace

from typing import Any, Awaitable, Callable, List, Optional

class IFaceDiscord(IFace):
    def __init__(self, commsChannel: discord.TextChannel):
        super().__init__()

        self.commsChannel = commsChannel
        self.message: Optional[discord.Message] = None

    def createButton(self, label: str, val: str, userID:int, callback: Callable[[str], Awaitable[None]]):
        return SimonButton(label, val, userID, callback)

    async def sendButtons(self, label: str, buttons: List[Any]):
        buttonView = discord.ui.View()
        for button in buttons:
            buttonView.add_item(button)

        self.message = await self.commsChannel.send(label, view=buttonView)

    async def confirmReact(self):
        if self.message:
            await self.message.add_reaction("\U00002705")


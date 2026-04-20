__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord

from abc import ABC, abstractmethod

class IMiscCommand(ABC):
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def getCommandName(self) -> str:
        pass

    @abstractmethod
    async def runCommand(self, interaction: discord.Interaction):
        pass


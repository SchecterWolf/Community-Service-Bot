__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord

from abc import ABC, abstractmethod
from typing import Dict, Optional

from .DiscordBailiff import DiscordBailiff
from .GuildStore import GuildStore

class ICommand(ABC):
    def __init__(self, **kwargs):
        self.bailiffs: Dict[int, DiscordBailiff] = dict()

    @abstractmethod
    def setupCommands(self, tree: discord.app_commands.CommandTree):
        pass

    def _getBailiff(self, serverID: int) -> Optional[DiscordBailiff]:
        ret = self.bailiffs.get(serverID, None)
        if not ret:
            ret = GuildStore().getBailiff(serverID)
            if ret:
                self.bailiffs[serverID] = ret

        return ret

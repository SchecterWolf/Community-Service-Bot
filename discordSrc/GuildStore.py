__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .DiscordBailiff import DiscordBailiff

from config.ClassLogger import ClassLogger, LogLevel

from typing import List, Optional

class GuildStore:
    __LOGGER = ClassLogger(__name__)
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        # Init guard
        if hasattr(self, "initialized"):
            return

        self.bailiffs: List[DiscordBailiff] = []
        self.initialized = True

    def addBailiff(self, bailiff: DiscordBailiff):
        if any(b.getID() == bailiff.getID() for b in self.bailiffs):
            GuildStore.__LOGGER.log(LogLevel.LEVEL_WARN, f"Guild store already has a bailiff for server ({bailiff.getID()}), skipping.")
        else:
            GuildStore.__LOGGER.log(LogLevel.LEVEL_INFO, f"Adding bailiff for server ({bailiff.getID()}) to the guild store.")
            self.bailiffs.append(bailiff)

    def getBailiff(self, serverID: int) -> Optional[DiscordBailiff]:
        return next((b for b in self.bailiffs if b.getID() == serverID),  None)


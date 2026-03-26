__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from abc import ABC, abstractmethod

from .Bailiff import Bailiff
from .InmateData import InmateData
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel

class ICommsGame(ABC):
    __LOGGER = ClassLogger(__name__)
    _HELP_CMD_STR = "\nUse the /help command for help."

    def __init__(self, name: str, inmate: InmateData, bailiff: Bailiff, reason: str):
        self.name = name
        self.inmate = inmate
        self.bailiff = bailiff
        self.reason = reason

    @abstractmethod
    async def start(self) -> Result:
        pass

    @abstractmethod
    async def addWork(self, userInput: str) -> Result:
        pass

    @abstractmethod
    async def finish(self) -> Result:
        pass

    @abstractmethod
    def getHelpInfo(self) -> str:
        pass

    async def _start(self):
        self.reason += "\n" + self.getHelpInfo() + "\n" + ICommsGame._HELP_CMD_STR
        await self.bailiff.speakToInmate(self.reason)

    async def _finish(self):
        infoStr = f"User \"{self.name}\" has finished counting, and is being released!"
        ICommsGame.__LOGGER.log(LogLevel.LEVEL_INFO, infoStr)
        await self.bailiff.speakToInmate(infoStr)
        await self.bailiff.releaseInmate(self.inmate, self.name)


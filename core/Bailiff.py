__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from abc import ABC, abstractmethod

from .IFace import IFace
from .InmateData import InmateData
from .Result import Result

from typing import Any

class Bailiff(ABC):
    @abstractmethod
    def getInterface(self) -> IFace:
        pass

    @abstractmethod
    async def commitInmate(self, inmate: InmateData, name: str) -> Result:
        pass

    @abstractmethod
    async def releaseInmate(self, inmate: InmateData, name: str):
        pass

    @abstractmethod
    async def speakToInmate(self, data: Any):
        pass


__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from abc import ABC, abstractmethod

from typing import Any, Awaitable, Callable, List

# TODO SCH This class should be more generic, but I don't forsee extending it to a new interface anytime soon.
# Therefore, I don't care enough.
class IFace(ABC):
    @abstractmethod
    def createButton(self, label: str, val: str, userID: int, callback: Callable[[str], Awaitable[None]]):
        pass

    @abstractmethod
    async def sendButtons(self, label: str, buttons: List[Any]):
        pass

    @abstractmethod
    async def confirmReact(self):
        pass


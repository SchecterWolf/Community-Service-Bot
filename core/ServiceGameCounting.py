__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .Bailiff import Bailiff
from .ICommsGame import ICommsGame
from .InmateData import InmateData
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel

class ServiceGameCounting(ICommsGame):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, name: str, inmateData: InmateData, bailiff: Bailiff, reason: str):
        super().__init__(name, inmateData, bailiff, reason)
        self.currentCount = -1

    async def start(self) -> Result:
        await self._start()
        return Result(result=True)

    async def addWork(self, userInput: str) -> Result:
        ServiceGameCounting.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"User \"{self.name}\" committed work to the game: {userInput}")
        ret = Result()
        try:
            val = int(userInput)
            if val == self.currentCount + 1:
                self.currentCount = val
                ret.result = True
            else:
                ret.errorStr = "\"userInput\" is not the correct next number"
        except:
            pass
        return ret

    async def finish(self) -> Result:
        if self.currentCount < self.inmate.rounds:
            return Result(errorStr="Inmate has not finished counting")

        await self._finish()
        return Result(True)

    def getHelpInfo(self) -> str:
        return f"\nYour community service task is to count up to {self.inmate.rounds} starting at 0." \
                + " One number number per message, incrementing by one for each new message." \
                + " Messages containing anything other than a number wont count! Once you finish counting" \
                + " you will be released from community service.\n" \
                + f"Your next counting number is {self.currentCount + 1}."


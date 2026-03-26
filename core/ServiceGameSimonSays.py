__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import random

from .Community import Community
from .Bailiff import Bailiff
from .ICommsGame import ICommsGame
from .InmateData import InmateData
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel

class ServiceGameSimonSays(ICommsGame):
    __LOGGER = ClassLogger(__name__)
    COLORS = {
        "red": "🟥",
        "blue": "🟦",
        "green": "🟩",
        "yellow": "🟨"
    }

    def __init__(self, name: str, inmateData: InmateData, bailiff: Bailiff, reason: str):
        super().__init__(name, inmateData, bailiff, reason)
        self.interface = bailiff.getInterface()
        self.currentCycle =0
        self.choiceColor = ""

    async def start(self) -> Result:
        await self._start()
        await self._sendNewChallenge()
        return Result(True)

    # This game does not accept user messages as work
    async def addWork(self, userInput: str) -> Result:
        return Result(False)

    async def finish(self) -> Result:
        if self.currentCycle < self.inmate.rounds:
            return Result(errorStr="Inmate has not finished following what simon says.")

        await self._finish()
        return Result(True)

    def getHelpInfo(self) -> str:
        return f"\nYour community service task is to follow what simon says for {self.inmate.rounds} rounds!" \
                + " Simon will speak a color and you must click on the button with the correct color emoji." \
                + " Once you finish following what simon says, you will be released from community service."

    async def _sendNewChallenge(self):
        self.choiceColor = random.choice(list(ServiceGameSimonSays.COLORS.keys())).capitalize()
        ServiceGameSimonSays.__LOGGER.log(LogLevel.LEVEL_INFO, f"Creating new simon says challenge for color: {self.choiceColor}")

        # Create the random order buttons
        items = list(ServiceGameSimonSays.COLORS.items())
        random.shuffle(items)
        buttons = []
        for color, emoji in items:
            buttons.append(self.interface.createButton(color, emoji, self.inmate.userid, self.__checkGuess))

        # Send buttons to the viewer
        await self.interface.sendButtons(f"Simon says: {self.choiceColor}", buttons)

    async def __checkGuess(self, color: str):
        if color != self.choiceColor:
            ServiceGameSimonSays.__LOGGER.log(LogLevel.LEVEL_INFO, f"User \"{self.name}\" chose the incorrect color.")
            await self._sendNewChallenge()
        else:
            ServiceGameSimonSays.__LOGGER.log(LogLevel.LEVEL_INFO, f"User \"{self.name}\" chose the correct color.")
            await self.interface.confirmReact()
            self.currentCycle += 1
            if self.currentCycle < self.inmate.rounds:
                await self._sendNewChallenge()
            else:
                await self.finish()
                # We have to manually remove the game from the community here since this game isnt cycled by messages
                # send by the user
                Community().removeServiceGame(self.inmate.serverid, self.inmate.userid)


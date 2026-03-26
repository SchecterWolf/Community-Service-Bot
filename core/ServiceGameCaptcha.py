__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord
import random

from captcha.image import ImageCaptcha
from io import BytesIO

from .Bailiff import Bailiff
from .ICommsGame import ICommsGame
from .InmateData import InmateData
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel

class ServiceGameCaptcha(ICommsGame):
    __LOGGER = ClassLogger(__name__)
    __CAPTCHA_LENGTH_MIN = 5
    __CAPTCHA_LENGTH_MAX = 10

    def __init__(self, name: str, inmateData: InmateData, bailiff: Bailiff, reason: str):
        super().__init__(name, inmateData, bailiff, reason)
        self.currentCycle = 0
        self.captchaGen = ImageCaptcha(width=400, height=160)
        self.captchaText: str = ""

    async def start(self) -> Result:
        await self._start()
        await self.__sendNewCaptcha()
        return Result(result=True)

    async def addWork(self, userInput: str) -> Result:
        ServiceGameCaptcha.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"User \"{self.name}\" committed work to the game: {userInput}")
        ret = Result()

        if self.captchaText != userInput:
            ret.errorStr = "\"{userInput}\" is not correct!"
            await self.bailiff.speakToInmate(ret.errorStr)
            await self.__sendNewCaptcha()
        else:
            ret.result = True
            self.currentCycle += 1
            if self.currentCycle < self.inmate.rounds:
                await self.__sendNewCaptcha()

        return ret

    async def finish(self) -> Result:
        if self.currentCycle < self.inmate.rounds:
            return Result(errorStr="Inmate has not finished solving all of the captchas.")

        await self._finish()
        return Result(True)

    def getHelpInfo(self) -> str:
        return f"\nYour community service task is to solve {self.inmate.rounds} captcha images!" \
                + " You will be presented a captcha image, and you must reply with the correct alphanumeric." \
                + " Once you finish all the captcha images, you will be released from community service."

    async def __sendNewCaptcha(self):
        self.captchaText = self.__generateAlphaNum()
        ServiceGameCaptcha.__LOGGER.log(LogLevel.LEVEL_INFO, f"Generating new captcha image for text \"{self.captchaText}\"")
        data: BytesIO = self.captchaGen.generate(self.captchaText)

        data.seek(0)
        file = discord.File(fp=data, filename="captcha.png")
        await self.bailiff.speakToInmate(file)

    def __generateAlphaNum(self) -> str:
        length = random.randint(ServiceGameCaptcha.__CAPTCHA_LENGTH_MIN, ServiceGameCaptcha.__CAPTCHA_LENGTH_MAX)
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return ''.join(random.choices(chars, k=length))


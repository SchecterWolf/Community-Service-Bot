__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import random

from .Bailiff import Bailiff
from .ICommsGame import ICommsGame
from .InmateData import InmateData
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel

class ServiceGameMath(ICommsGame):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, name: str, inmateData: InmateData, bailiff: Bailiff, reason: str):
        super().__init__(name, inmateData, bailiff, reason)
        self.currentCycle = 0
        self.correctAnswer: int = 0

    async def start(self) -> Result:
        await self._start()
        await self.__genProblem()
        return Result(True)

    async def addWork(self, userInput: str) -> Result:
        ServiceGameMath.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"USer \"{self.name}\" committed work to the game: {userInput}")
        ret = Result()
        try:
            val = int(userInput)
            if val != self.correctAnswer:
                ret.errorStr = f"\"{userInput}\" is not correct! The correct answer was: {self.correctAnswer}"
                await self.bailiff.speakToInmate(ret.errorStr)
                await self.__genProblem()
            else:
                ret.result = True
                self.currentCycle += 1
                if self.currentCycle < self.inmate.rounds:
                    await self.__genProblem()
        except:
            pass
        return ret

    async def finish(self) -> Result:
        if self.currentCycle < self.inmate.rounds:
            return Result(errorStr="Inmate has not finished doing his math problems!")

        await self._finish()
        return Result(True)

    def getHelpInfo(self) -> str:
        return f"\nYour community service task is to solve {self.inmate.rounds} rounds of math problems!" \
                + " You will be presented with a simple math problem, and you must reply with the correct answer (to the nearest 2 decimal places)." \
                + " Once you finish all the math problems, you will be released from community service."

    async def __genProblem(self):
        num_count = random.randint(2, 4)
        numbers = [random.randint(1, 10) for _ in range(num_count)]
        operators = [random.choice(["+", "-", "*", "/"]) for _ in range(num_count - 1)]

        expression = str(numbers[0])

        for i in range(len(operators)):
            op = operators[i]
            num = numbers[i + 1]

            # Prevent messy division
            if op == "/":
                # force divisible numbers
                prev = eval(expression)
                num = random.randint(1, 10)
                prev = int(prev)
                num = random.randint(1, 10)
                prev = prev * num  # ensures clean division
                expression = str(prev)

            expression += f" {op} {num}"

        try:
            answer = eval(expression)
        except ZeroDivisionError:
            return self.__genProblem()

        self.correctAnswer = round(answer, 2)
        await self.bailiff.speakToInmate(f"{expression} = ?")


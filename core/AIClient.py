__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

from openai import OpenAI
from typing import Optional

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS

class AIClient:
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

        self.client: Optional[OpenAI] = None
        self.initialized = True

    def getClient(self) -> OpenAI:
        if self.client is None:
            self.client = self.__makeNewClient()
        return self.client

    def __makeNewClient(self) -> OpenAI:
        AIClient.__LOGGER.log(LogLevel.LEVEL_WARN, f"Creating new Open AI client.")

        token = ""
        with open(f"{GLOBALVARS.FILE_OPENAI_TOKEN}") as file:
            token = file.readline().strip()
        return OpenAI(api_key=token)


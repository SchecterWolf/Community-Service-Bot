__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .ICommsGame import ICommsGame

from config.ClassLogger import ClassLogger, LogLevel

from typing import List, Optional

class Community:
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

        self.activeGames: List[ICommsGame] = []
        self.initialized = True

    def checkUserGame(self, userID: int) -> bool:
        return any(g.inmate.userid == userID for g in self.activeGames)

    def addServiceGame(self, game: ICommsGame):
        if self.checkUserGame(game.inmate.userid):
            Community.__LOGGER.log(LogLevel.LEVEL_ERROR, f"User \"{game.inmate.userid}\" is already serving comms, skipping adding new comms for the user.")
        else:
            self.activeGames.append(game)

    def getServiceGame(self, serverID: int, inmateID: int) -> Optional[ICommsGame]:
        return next((g for g in self.activeGames if g.inmate.serverid == serverID and g.inmate.userid == inmateID), None)

    def removeServiceGame(self, serverID: int, inmateID: int):
        game = self.getServiceGame(serverID, inmateID)
        if not game:
            Community.__LOGGER.log(LogLevel.LEVEL_WARN, f"Cannot remove community service game for user ({inmateID}) "
                                   + f"in server ({serverID}) because it does not exist.")
        else:
            Community.__LOGGER.log(LogLevel.LEVEL_INFO, f"Removed community service game for user ({inmateID}) "
                                   + f"in server ({serverID}).")
            self.activeGames.remove(game)


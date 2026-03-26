__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

from .Bailiff import Bailiff
from .CommType import CommType
from .ICommsGame import ICommsGame
from .InmateData import InmateData
from .ServiceGameCaptcha import ServiceGameCaptcha
from .ServiceGameCounting import ServiceGameCounting
from .ServiceGameMath import ServiceGameMath
from .ServiceGameSimonSays import ServiceGameSimonSays

def createServiceGame(inmateName: str, inmateData: InmateData, bailiff: Bailiff, reason: str ) -> ICommsGame:
    ret = None

    if inmateData.mode is CommType.CAPTCHA:
        ret = ServiceGameCaptcha(inmateName, inmateData, bailiff, reason)
    elif inmateData.mode is CommType.SIMON:
        ret  = ServiceGameSimonSays(inmateName, inmateData, bailiff, reason)
    elif inmateData.mode is CommType.MATH:
        ret = ServiceGameMath(inmateName, inmateData, bailiff, reason)

    # Counting is the default game
    if ret is None:
        ret = ServiceGameCounting(inmateName, inmateData, bailiff, reason)

    return ret

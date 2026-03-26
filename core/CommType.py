__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from enum import IntEnum

class CommType(IntEnum):
    COUNT = 1
    CAPTCHA = 2
    SIMON = 3
    MATH = 4

    @property
    def label(self) -> str:
        return {
            CommType.COUNT: "Forward counting",
            CommType.CAPTCHA: "Captcha",
            CommType.SIMON: "Simon says",
            CommType.MATH: "Perform math",
        }[self]


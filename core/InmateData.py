__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import time

from .CommType import CommType

from dataclasses import dataclass, field
from typing import Set

@dataclass
class InmateData:
    id: int = 0
    serverid: int = 0
    userid: int = 0
    roles: Set[int] = field(default_factory=set)
    mode: CommType = CommType.COUNT
    rounds: int = 0
    timestamp: float = field(default_factory=time.time)

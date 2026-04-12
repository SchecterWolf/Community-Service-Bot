__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import subprocess
from pathlib import Path

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS

_VERSION = "0.3.2"

class Version:
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        self.repo = Path(GLOBALVARS.PROJ_ROOT)

    def getFullVersion(self) -> str:
        return f"v{_VERSION} - {self.getHash()}"

    def getHash(self) -> str:
        ret = "0000000"
        if not self.repo.exists():
            Version.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Error locating project root dir.")
            return ret

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short=7", "HEAD"],
                cwd=self.repo,
                capture_output=True,
                text=True,
                check=True
            )
            ret = result.stdout.strip()
        except Exception as e:
            Version.__LOGGER.log(LogLevel.LEVEL_CRIT, str(e))

        return ret


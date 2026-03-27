__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from pathlib import Path

class GLOBALVARS:
    PROJ_ROOT = str(Path(__file__).parent.parent)

    DIR_RESOURCES = PROJ_ROOT + "/resources"
    DIR_DATA = DIR_RESOURCES + "/data"
    DIR_CONFIG = PROJ_ROOT + "/config"

    FILE_BOT_VERSION = DIR_DATA + "/version.txt"
    FILE_CONFIG_GENERAL = DIR_CONFIG + "/config.json"
    FILE_DB = DIR_DATA + "/data.sqlite"
    FILE_TOKEN = DIR_CONFIG + "/token.txt"

    CONFIG_SLASH_INIT = "slash_init"
    CONFIG_HASH = "bot_hash"


__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from core.CommType import CommType

class CommsTypeSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for commType in CommType:
            options.append(
                discord.SelectOption(label=commType.label, value=str(commType))
            )

        super().__init__(options=options, min_values=1)

    def getType(self) -> CommType:
        ret = CommType.COUNT
        if len(self.values) > 0:
            ret = CommType(int(self.values[0]))

        return ret


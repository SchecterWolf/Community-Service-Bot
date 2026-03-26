#!/usr/bin/env python3
__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio
import signal
import sys

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config

from discordSrc.Bot import Bot

def main():
    logger = ClassLogger("Main")
    logger.log(LogLevel.LEVEL_INFO, "Community service bot is starting up...")

    bot = Bot()
    closeTriggered = False

    def singalCloseWrapper(sig, frame):
        logger.log(LogLevel.LEVEL_CRIT, "SIGINT or SIGTERM received, attempting to shut down...")

        nonlocal closeTriggered
        if closeTriggered:
            sys.exit(0)

        loop = asyncio.get_event_loop()
        if loop:
            loop.create_task(bot.stopBot())
        closeTriggered = True

    signal.signal(signal.SIGINT, singalCloseWrapper)
    signal.signal(signal.SIGTERM, singalCloseWrapper)

    bot.runBot()

if __name__ == '__main__':
    main()

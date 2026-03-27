__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .DiscordBailiff import DiscordBailiff
from .CommandHandler import CommandHandler
from .GuildStore import GuildStore
from .MoveMessage import MoveMessage

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

from core.Community import Community
from core.DB import DB
from core.Version import Version

from discord.client import Client

from typing import List

class Bot(Client):
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

        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(intents=intents)

        self.commandHandler = CommandHandler()
        self.moveMessageHandler = MoveMessage(self)
        self.initialized = True
        self.commsChannels: List[int] = []
        self.printVersion = False

    def runBot(self):
        token = ""
        with open(f"{GLOBALVARS.FILE_TOKEN}") as file:
            token = file.readline()
        self.run(token, root_logger=True) # Blocks

    async def stopBot(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, "Shutting down the community service bot...")
        await self.close()

    async def setup_hook(self):
        db = DB(0)
        self.tree = discord.app_commands.CommandTree(self)

        self.commandHandler.setupCommands(self.tree)
        self.moveMessageHandler.setupCommands(self.tree)
        if not db.getConfigAttr(GLOBALVARS.CONFIG_SLASH_INIT, int, 0):
            Bot.__LOGGER.log(LogLevel.LEVEL_WARN, f">>>>>>Syncing slash commands!")
            try:
                await self.tree.sync()
                # Set the sync config flag to true now that the slash commands are synced
                db.setConfigAttr(GLOBALVARS.CONFIG_SLASH_INIT, 1)
            except Exception as e:
                Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Failed to sync bot commands: {e}")

    async def on_ready(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_INFO, f"Discord bot logged in as {self.user}")

        db = DB(0)
        version = Version()
        if db.getConfigAttr(GLOBALVARS.CONFIG_HASH, str, "") != version.getHash():
            db.setConfigAttr(GLOBALVARS.CONFIG_HASH, version.getHash())
            self.printVersion = True

        for guild in self.guilds:
            await self.on_guild_join(guild)

        self.printVersion = False

    async def on_guild_join(self, guild: discord.Guild):
        Bot.__LOGGER.log(LogLevel.LEVEL_INFO, f"Initializing guild: {guild.name}")

        bailiff = None
        commsChannelID = Config().getConfig(guild.id, 'CommunityServiceChannel', 0)
        commsChannel = guild.get_channel(commsChannelID)

        if not commsChannelID:
            Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Server \"{guild.name}\" needs a channel ID for the community service channel configured! Skipping setup for this server!")
        elif not commsChannel:
            Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Could not find community service channel for ID \"{commsChannelID}\", skipping setup for server \"{guild.name}\"")
        elif not isinstance(commsChannel, discord.TextChannel):
            Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Community service channel \"{commsChannel.name}\" need to be a text channel, skipping setup for server \"{guild.name}\"")
        else:
            bailiff = DiscordBailiff(guild, commsChannel)
            GuildStore().addBailiff(bailiff)
            self.commsChannels.append(commsChannelID)

            # Release all inmate in the DB, in case the bot crashed and it rebooted
            inmates = DB(guild.id).getAllInmates()
            if inmates:
                Bot.__LOGGER.log(LogLevel.LEVEL_INFO, f"Bot recovery, releasing all inmates in the \"{guild.name}\" server...")
            for inmate in inmates:
                await bailiff.releaseInmate(inmate, str(inmate.userid))

        # Print bot version if it changed
        version = Version()
        if bailiff and self.printVersion:
            await bailiff.channelCommunityService.send(f"Bot restarted\n{version.getFullVersion()}")

    async def on_disconnect(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, "The community service bot has been disconnected.")

    async def on_message(self, message: discord.Message):
        # Boilerplate checking
        if message.author.bot or not message.guild or message.channel.id not in self.commsChannels:
            return

        game = Community().getServiceGame(message.guild.id, message.author.id)
        finished = False
        if game:
            ret = await game.addWork(message.content)
            if ret.result:
                await message.add_reaction("\U00002705")
                finished = (await game.finish()).result

        if finished:
            Community().removeServiceGame(message.guild.id, message.author.id)


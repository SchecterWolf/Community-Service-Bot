__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IFaceDiscord import IFaceDiscord

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config

from core.Bailiff import Bailiff
from core.DB import DB
from core.IFace import IFace
from core.InmateData import InmateData
from core.Result import Result

from typing import Any, List

class DiscordBailiff(Bailiff):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, server: discord.Guild, channelCommunityService: discord.channel.TextChannel):
        self.server = server
        self.DB = DB(server.id)
        self.channelCommunityService = channelCommunityService
        self.commsRole = server.get_role(Config().getConfig(server.id, 'CommunityServiceRole', 0))
        self.allowEmptyRoles = Config().getConfig(server.id, 'AllowEmptyRoles', False)

    def getID(self) -> int:
        return self.server.id

    def getInterface(self) -> IFace:
        return IFaceDiscord(self.channelCommunityService)

    async def commitInmate(self, inmate: InmateData, name: str) -> Result:
        DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_INFO, f"Commiting user \"{name}\" to community service...")
        member = self.server.get_member(inmate.userid)

        # Error check
        if not self.commsRole:
            return Result(errorStr="Invalid community service role configured.")
        elif not inmate.roles and not self.allowEmptyRoles:
            return Result(errorStr="User has no roles, there might have been an issue reading them in.")
        elif not member:
            return Result(errorStr=f"Could not locate user \"{name}\", aborting,")
        elif self.DB.getInmate(inmate.userid):
            return Result(errorStr=f"User \"{name}\" is already in community service!")

        # Make sure that the role IDs cant be fetched properly
        for roleID in inmate.roles:
            role = self.server.get_role(roleID)
            if not role:
                return Result(errorStr=f"Role ({roleID}) could not be located. Aborting for safety.")

        # Check for the special booster role
        commsRoles=[self.commsRole]
        for role in member.roles:
            if role.is_premium_subscriber():
                commsRoles.append(role)

        # Re-assign the roles
        try:
            await member.edit(roles=commsRoles)
            pass
        except discord.Forbidden:
            return Result(errorStr=f"User \"{name}\" is too powerfull, I cannot change their roles.")
        except Exception as e:
            return Result(errorStr=str(e))

        # Add inmate to DB
        self.DB.saveInmate(inmate)

        return Result(result=True)

    async def releaseInmate(self, inmate: InmateData, name: str):
        DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_INFO, f"Releasing \"{name}\" from community service....")
        member = self.server.get_member(inmate.userid)
        currentRoles = member.roles if member else []

        # Error check
        if not member:
            DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Could not locate user \"{name}\" from the server members, aborting.")
            return
        elif not self.commsRole:
            DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Invalid community service role configured.")
            return
        elif not currentRoles or currentRoles[0].id == self.commsRole.id:
            DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_ERROR, f"User appears not to be currently serving community service, aborting.")
            return

        # Get all the saved user roles
        userRoles: List[discord.Role] = []
        for roleID in inmate.roles:
            role = self.server.get_role(roleID)
            if role:
                userRoles.append(role)

        # Assign the user all of their former roles
        removeFromDB = True
        try:
            DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Assigning user \"{name}\"({inmate.userid}) their former roles: {userRoles}")
            await member.edit(roles=userRoles)
            pass
        except Exception as e:
            DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Role assignment error: {e}")
            DiscordBailiff.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Could not assign user back their roles of: {userRoles}")
            removeFromDB = False

        # Remove inmate from DB
        if removeFromDB:
            self.DB.deleteInmate(inmate.userid)

    async def speakToInmate(self, data: Any):
        if isinstance(data, str):
            await self.channelCommunityService.send(data)
        elif isinstance(data, discord.File):
            await self.channelCommunityService.send(file=data)
        elif isinstance(data, discord.ui.View):
            await self.channelCommunityService.send(view=data)
        else:
            raise ValueError(f"Unexpected data type received: {type(data)}")


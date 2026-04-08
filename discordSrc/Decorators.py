__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
from config.Config import Config
from functools import wraps

def require_jailmod(func):
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction):
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            roleID = Config().getConfig(interaction.guild_id or 0, "JailMod", 0)
            role = interaction.guild.get_role(roleID)
            if not member or not any(roleID == role.id for role in member.roles):
                await interaction.response.send_message(f"\U0000274C The role of \"{role.name if role else 'JailMod'}\" is required to use this feature.", ephemeral=True)
                return None
        return await func(self, interaction)
    return wrapper

async def verifyIsJailmod(interaction: discord.Interaction) -> bool:
    return await verifyIsRole(interaction, 'JailMod')

async def verifyIsListRoles(interaction: discord.Interaction, configListRole: str, errStr: str) -> bool:
    if not interaction.guild:
        await interaction.response.send_message("Could not validate server ID")
        return False

    member = interaction.guild.get_member(interaction.user.id)
    listRoles = Config().getConfig(interaction.guild_id or 0, configListRole, [])
    if not any(checkRole(roleID, member) for roleID in listRoles):
        await interaction.response.send_message(errStr, ephemeral=True)
        return False
    return True

async def verifyIsRole(interaction: discord.Interaction, configRole: str) -> bool:
    if not interaction.guild:
        await interaction.response.send_message("Could not validate server ID")
        return False

    member = interaction.guild.get_member(interaction.user.id)
    roleID = Config().getConfig(interaction.guild_id or 0, configRole, 0)
    if not checkRole(roleID, member):
        role = interaction.guild.get_role(roleID)
        await interaction.response.send_message(f"\U0000274C The role of \"{role.name if role else configRole}\" is required to use this feature.", ephemeral=True)
        return False
    return True

def checkRole(roleID: int, member: discord.Member | None) -> bool:
    return member != None and any(roleID == role.id for role in member.roles)


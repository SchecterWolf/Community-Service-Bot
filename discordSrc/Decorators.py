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
    if not interaction.guild:
        return False

    member = interaction.guild.get_member(interaction.user.id)
    roleID = Config().getConfig(interaction.guild_id or 0, "JailMod", 0)
    role = interaction.guild.get_role(roleID)
    if not member or not any(roleID == role.id for role in member.roles):
        await interaction.response.send_message(f"\U0000274C The role of \"{role.name if role else 'JailMod'}\" is required to use this feature.", ephemeral=True)
        return False
    return True


__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .CommsPropertiesModal import CommsPropertiesModal
from .GuildStore import GuildStore
from .ICommand import ICommand

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config

from core.Community import Community
from core.DB import DB

from discord import Interaction, Member
from discord.app_commands import CommandTree
from discord.app_commands.commands import Command
from discord.app_commands.errors import AppCommandError

from discordSrc.Decorators import verifyIsJailmod

from typing import List

class CommandHandler(ICommand):
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        super().__init__()

        self.listCommands: List[Command]= [
            Command(
                name="give_comms",
                description="[ADMIN] Send a user to community service",
                callback=self.giveComms
            ),
            Command(
                name="help",
                description="Community service help information",
                callback=self.getHelp
            ),
            Command(
                name="echo",
                description="[ADMIN] Send a message anonymously as the bot",
                callback=self.echo
            ),
            Command(
                name="release",
                description="[ADMIN] Release someone from comms",
                callback=self.release
            )
        ]

    def setupCommands(self, tree: CommandTree):
        CommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Initializing the command handler commands...")
        for cmd in self.listCommands:
            cmd.on_error = self.errorHandler
            tree.add_command(cmd)

    async def errorHandler(self, _, interaction: Interaction, error: AppCommandError):
        if interaction.command:
            CommandHandler.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Handler error called for command \"{interaction.command.name}\": {error}")
        else:
            CommandHandler.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Handler error called for unknown command: {error}")

        if isinstance(error, discord.app_commands.errors.MissingRole):
            await interaction.response.send_message("\U0000274C You do not have permission to use this command!", ephemeral=True)
        else:
            await interaction.response.send_message(f"Could not process command: {error}", ephemeral=True)

    @discord.app_commands.describe(member="User to send to comms")
    async def giveComms(self, interaction: Interaction, member: Member):
        CommandHandler.__LOGGER.log(LogLevel.LEVEL_INFO, f"\"{interaction.user.display_name}\" invoked the give_comms command.")
        bailiff = self._getBailiff(interaction.guild_id or 0)

        # Error check
        if not await verifyIsJailmod(interaction):
            pass
        elif not member:
            await interaction.response.send_message("Could not locate member for some reason....", ephemeral=True)
        elif member.bot:
            await interaction.response.send_message("Cannot give community service to a bot!", ephemeral=True)
        elif not bailiff:
            await interaction.response.send_message(f"Failed to properly initialize the server. Aborting.", ephemeral=True)
        elif Community().checkUserGame(member.id):
            await interaction.response.send_message(f"User \"{member.global_name}\" is already serving community service! Skipping!", ephemeral=True)
        else:
            await interaction.response.send_modal(CommsPropertiesModal(member, bailiff))

    @discord.app_commands.describe(message="Message to repeat back anonymously as the bot")
    @discord.app_commands.describe(reply_id="(Optional) message ID to reply to")
    async def echo(self, interaction: Interaction, message: str, reply_id: str | None):
        CommandHandler.__LOGGER.log(LogLevel.LEVEL_INFO, f"\"{interaction.user.display_name}\" invoked the echo command.")

        # Error check
        if not await verifyIsJailmod(interaction):
            return
        elif not interaction.channel or not isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
            await interaction.response.send_message("Something went wrong.")
            return

        await interaction.response.send_message("\u200b", ephemeral=True)

        if not reply_id:
            await interaction.channel.send(message, allowed_mentions=discord.AllowedMentions.all())
        else:
            try:
                replyMsg = await interaction.channel.fetch_message(int(reply_id))
                await replyMsg.reply(message, allowed_mentions=discord.AllowedMentions.all())
            except Exception as e:
                await interaction.followup.send(str(e), ephemeral=True)

    @discord.app_commands.describe(member="User to release")
    async def release(self, interaction: Interaction, member: Member):
        CommandHandler.__LOGGER.log(LogLevel.LEVEL_INFO, f"\"{interaction.user.display_name}\" invoked the release command.")
        overrides = Config().getConfig(interaction.guild_id or 0, "Override", [])

        # Error check
        if not any(interaction.user.id == o for o in overrides):
            if not await verifyIsJailmod(interaction):
                return

        userID = member.id
        game = Community().getServiceGame(interaction.guild_id or 0, userID)

        # Force finish the user's game
        if game:
            await interaction.response.send_message(f"Releasing user \"{member.name}\" from comms.")
            await game._finish()
            Community().removeServiceGame(interaction.guild_id or 0, userID)
        # Try from the DB
        else:
            db = DB(member.guild.id)
            inmate = db.getInmate(userID)
            bailiff = GuildStore().getBailiff(member.guild.id)

            if inmate and bailiff:
                await bailiff.releaseInmate(inmate, member.name)
            # Notify the user isn't serving comms
            else:
                logStr = f"User \"{member.display_name}\" is currently not service community service."
                CommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, logStr)
                await interaction.response.send_message(logStr)

    async def getHelp(self, interaction: Interaction):
        game = Community().getServiceGame(interaction.guild_id or 0, interaction.user.id)
        if not game:
            await interaction.response.send_message("You do not have any community service.", ephemeral=True)
        else:
            await interaction.response.send_message(game.getHelpInfo(), ephemeral=True)


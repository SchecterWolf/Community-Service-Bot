__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .Decorators import verifyIsJailmod
from .ICommand import ICommand

from config.ClassLogger import ClassLogger, LogLevel

class MoveMessage(discord.app_commands.ContextMenu, ICommand):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client):
        super().__init__(name="Move Message", callback=self.callback, type=discord.AppCommandType.message)
        self.bot = bot

    def setupCommands(self, tree: discord.app_commands.CommandTree):
        MoveMessage.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Initializing the move message command.")
        tree.add_command(self)

    async def callback(self, interaction: discord.Interaction, message: discord.Message):
        MoveMessage.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Move message command invoked by user \"{interaction.user.display_name}\"")
        if not await verifyIsJailmod(interaction):
            return

        try:
            sourceChannel = interaction.channel

            # Prompt for the move channel
            await interaction.response.send_message("Mention the channel to move the message to.", ephemeral=True)

            # Check predicate
            def check(m: discord.Message):
                return m.author == interaction.user and m.channel == interaction.channel

            # Wait for response
            reply = await self.bot.wait_for("message", check=check, timeout=60)

            # Parse channel mention
            targetChannel = reply.channel_mentions[0]
            if not isinstance(targetChannel, discord.TextChannel):
                await interaction.followup.send("Invalid channel.", ephemeral=True)
                return

            # Create the embed
            embed = discord.Embed(description=message.content, color=discord.Color.blurple())
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            if isinstance(sourceChannel, discord.TextChannel):
                embed.set_footer(text=f"Message moved from {sourceChannel.name}")
            embed.timestamp = message.created_at

            # Send to target channel
            await targetChannel.send(embed=embed)

            # Delete original message
            await reply.delete()
            await message.delete()

            await interaction.followup.send("Message moved!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)


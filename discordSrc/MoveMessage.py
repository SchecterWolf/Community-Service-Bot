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
from .MoveMessageModal import MoveMessageModal

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
        elif not interaction.guild:
            MoveMessage.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Move message interaction received an empty guild.")
            return

        try:
            # Prompt for transfer channel
            modal = MoveMessageModal()
            await interaction.response.send_modal(modal)
            timedOut = await modal.wait()
            if timedOut:
                await interaction.followup.send("Timed out waiting for channel selection.", ephemeral=True)
                return

            # Retrieve the transfer channel
            selected = modal.selectedChannel
            if selected is None:
                await interaction.followup.send("No channel selected.", ephemeral=True)
                return
            targetChannel = interaction.guild.get_channel(selected.id)
            if targetChannel is None:
                try:
                    targetChannel = await interaction.guild.fetch_channel(selected.id)
                except Exception:
                    targetChannel = None
            if not isinstance(targetChannel, discord.TextChannel):
                MoveMessage.__LOGGER.log(LogLevel.LEVEL_ERROR, "Could not retrieve an appropriate target channel to move the message to.")
                await interaction.followup.send("Invalid channel.", ephemeral=True)
                return
            sourceName = interaction.channel.name if isinstance(interaction.channel, discord.TextChannel) else "unknown-channel"

            # Re-upload any attachments so images/files survive the move
            files: list[discord.File] = []
            for attachment in message.attachments:
                try:
                    files.append(await attachment.to_file())
                except Exception as e:
                    MoveMessage.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Failed to convert attachment \"{attachment.filename}\" to file: {e}")

            # Set up the embed
            movedEmbed = discord.Embed(color=discord.Color.blurple())
            movedEmbed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            movedEmbed.set_footer(text=f"Message moved from {sourceName}")

            # Put original text in the embed body
            descriptionParts = []
            if message.content:
                descriptionParts.append(message.content)

            # If there was no text, try to preserve useful info from embeds like gifs/links/images
            # This helps for link-only / tenor-style messages when possible.
            if not descriptionParts and message.embeds:
                for originalEmbed in message.embeds:
                    if originalEmbed.url:
                        descriptionParts.append(originalEmbed.url)

                    if originalEmbed.description:
                        descriptionParts.append(originalEmbed.description)

                    # Sometimes link/gif embeds have a title worth showing
                    if originalEmbed.title:
                        descriptionParts.append(f"**{originalEmbed.title}**")

                    # Stop after first embed that gives us something useful
                    if descriptionParts:
                        break

            movedEmbed.description = "\n\n".join(descriptionParts) if descriptionParts else ""

            # If there is an attached image, show the first one inline in the embed
            firstImageUrl = None
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    firstImageUrl = f"attachment://{attachment.filename}"
                    break

            if firstImageUrl:
                movedEmbed.set_image(url=firstImageUrl)
            else:
                # Fall back to images/thumbnails from original embeds where possible
                for originalEmbed in message.embeds:
                    if originalEmbed.image and originalEmbed.image.url:
                        movedEmbed.set_image(url=originalEmbed.image.url)
                        break
                    if originalEmbed.thumbnail and originalEmbed.thumbnail.url:
                        movedEmbed.set_thumbnail(url=originalEmbed.thumbnail.url)
                        break

            movedEmbed.timestamp = message.created_at

            MoveMessage.__LOGGER.log(LogLevel.LEVEL_INFO, f"Message ID \"{message.id}\" was moved to channel {targetChannel.name}.")
            await targetChannel.send(embed=movedEmbed, files=files if files else [], allowed_mentions=discord.AllowedMentions.none())
            await message.delete()

            await interaction.followup.send("Message moved!", ephemeral=True)

        except TimeoutError:
            await interaction.followup.send("Timed out waiting for channel mention.", ephemeral=True)

        except Exception as e:
            MoveMessage.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Move message failed: {e}")
            #await interaction.followup.send(f"Error: {e}", ephemeral=True)


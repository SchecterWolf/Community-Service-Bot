__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord

from datetime import datetime, timedelta
from openai import OpenAI
from typing import List, Optional, Tuple

from .ICommand import ICommand

from config.ClassLogger import ClassLogger, LogLevel
from core.AIClient import AIClient

class CommandSummarize(ICommand):
    __LOGGER = ClassLogger(__name__)
    __MESSAGE_CHUNK_MAX = 12000
    __MESSAGES_COUNT_MAX = 500
    __OUTPUT_SIZE_MAX = 2000
    __COOLDOWN_SEC = 1200.0

    def __init__(self):
        super().__init__()

        self.client: Optional[OpenAI] = None
        self.model = "gpt-4.1-mini"
        #self.model = "gpt-4.1"
        self.contextWrapper: Optional[discord.app_commands.ContextMenu] = None

        self.command = discord.app_commands.Command(
            name="sumz",
            description="Summarize a specified number of messages in the channel this command is called from.",
            callback=self.summarize,
        )
        self.command.error(CommandSummarize.generateError)

    def setupCommands(self, tree: discord.app_commands.CommandTree):
        CommandSummarize.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Initializing the summarize command.")

        self.client = AIClient().getClient()

        # Add the command to the tree
        tree.add_command(self.command)

        # Create a context menu wrapper
        @discord.app_commands.checks.cooldown(1, CommandSummarize.__COOLDOWN_SEC, key=lambda i: f"sumz_channel_{i.channel_id or 0}_user_{i.user.id}")
        async def cooldownWrapper(interaction: discord.Interaction, message: discord.Message):
            await self.summarizeFromContext(interaction, message)
        self.contextWrapper = discord.app_commands.ContextMenu(name="Summarize 2 Here",
                                                               callback=cooldownWrapper,
                                                               type=discord.AppCommandType.message)
        self.contextWrapper.error(self.generateError)
        tree.add_command(self.contextWrapper)

    async def summarizeFromContext(self, interaction: discord.Interaction, message: discord.Message):
        if self.client is None:
            await interaction.response.send_message("The AI client is not initialized.", ephemeral=True)
            return
        elif interaction.channel is None:
            await interaction.response.send_message("Could not determine the channel for this command.", ephemeral=True)
            return
        elif not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("This command can only be used in a text channel.", ephemeral=True)
            return
        elif message.channel.id != interaction.channel.id:
            await interaction.response.send_message("The selected message is not in this channel.", ephemeral=True)
            return

        CommandSummarize.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"User {interaction.user.name} used summarizeFromContext on message id={message.id}")
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            messages: List[discord.Message] = []

            async for msg in interaction.channel.history(limit=CommandSummarize.__MESSAGES_COUNT_MAX, oldest_first=False):
                # Skip the slash/context interaction backing message if one exists
                if interaction.message is not None and msg.id == interaction.message.id:
                    continue

                messages.append(msg)

                # Stop once we reached the selected message
                if msg.id == message.id:
                    break

            # history() returned newest -> oldest, so if the selected message
            # was not encountered, it means it is older than the max window.
            if not messages or messages[-1].id != message.id:
                await interaction.followup.send(
                    f"The selected message is too old. I can only summarize up to the last "
                    f"{CommandSummarize.__MESSAGES_COUNT_MAX} messages.",
                    ephemeral=True
                )
                return

            messages.reverse()

            # Summarize the message history
            summary = await self.__summarizeMessages(messages)
            if not summary:
                await interaction.followup.send("Failed to generate a summary.", ephemeral=True)
                return

            # Send the summary to the user
            header = (
                f"**Summary of {len(messages)} message(s) "
                f"from [selected message] to now:**\n\n"
            )
            output = header + summary
            await self.__sendSummaryDM(interaction, output)
            await interaction.channel.send(f"__**Summarize command**__: {len(messages)} message summary has sent to your DMs, {interaction.user.mention}.")

        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
        except Exception as e:
            CommandSummarize.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Unhandled summarizeFromContext exception: {e}")
            await interaction.followup.send("An unexpected error occurred while summarizing the channel.", ephemeral=True)

    @discord.app_commands.checks.cooldown(1, __COOLDOWN_SEC, key=lambda i: f"sumz_channel_{i.channel_id or 0}_user_{i.user.id}")
    @discord.app_commands.describe(start="Starting point to summarize. Can be a number, or a time like 3:15 PM or 15:15.")
    async def summarize(self, interaction: discord.Interaction, start: str):
        if self.client is None:
            await interaction.response.send_message("The AI client is not initialized.", ephemeral=True)
            return
        elif interaction.channel is None:
            await interaction.response.send_message("Could not determine the channel for this command.", ephemeral=True)
            return
        elif not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("This command can only be used in a text channel.", ephemeral=True)
            return

        CommandSummarize.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"User {interaction.user.name} used the summarize command with: {start}")
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            mode, count, after_dt = self.__parseStartArg(start)

            # Get the channel messages
            messages = await self.__collectMessages(channel=interaction.channel, mode=mode, count=count, after_dt=after_dt,
                                                    interaction=interaction)
            if not messages:
                await interaction.followup.send("No messages were found to summarize.", ephemeral=True)
                return

            # Create message summary
            summary = await self.__summarizeMessages(messages)
            if not summary:
                await interaction.followup.send("Failed to generate a summary.", ephemeral=True)
                return

            # Send the summary to the channel
            header = f"**Summary of {len(messages)} message(s):**\n\n"
            output = header + summary
            await self.__sendSummaryDM(interaction, output)
            await interaction.channel.send(f"__**Summarize command**__: {len(messages)} message summary has sent to your DMs, {interaction.user.mention}.")

        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
        except Exception as e:
            CommandSummarize.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Unhandled summarize exception: {e}")
            await interaction.followup.send("An unexpected error occurred while summarizing the channel.", ephemeral=True)

    async def generateError(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"This command is on cooldown in this channel. Try again in {error.retry_after:.0f} seconds.", ephemeral=True)
            return

        CommandSummarize.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Unhandled command error: {error}")

    async def __sendSummaryDM(self, interaction: discord.Interaction, output: str):
        try:
            dm_channel = interaction.user.dm_channel
            if dm_channel is None:
                dm_channel = await interaction.user.create_dm()

            chunks = self.__splitForDiscord(output, CommandSummarize.__OUTPUT_SIZE_MAX)
            for chunk in chunks:
                await dm_channel.send(chunk)

            await interaction.followup.send("I sent the summary to your DMs.", ephemeral=True)

        except discord.Forbidden:
            raise ValueError("I couldn't DM you. Please enable Direct Messages from server members and try again.")

    def __parseStartArg(self, start: str) -> Tuple[str, Optional[int], Optional[datetime]]:
        """
        Returns:
            (mode, count, after_dt)

        mode:
            "count" -> count is set
            "time"  -> after_dt is set
        """
        start = start.strip()

        # Handle number arg
        if start.isdigit():
            count = int(start)
            if count <= 0:
                raise ValueError("Message count must be greater than 0.")
            if count > CommandSummarize.__MESSAGES_COUNT_MAX:
                raise ValueError(f"Please choose {CommandSummarize.__MESSAGES_COUNT_MAX} messages or fewer.")
            return ("count", count, None)

        # Handle time arg
        parsed_time = self.__parseTimeString(start)
        if parsed_time is None:
            raise ValueError("Invalid start format. Use either a number like `50`, or a time like `3:15 PM` or `15:15`.")

        now = datetime.now().astimezone()
        after_dt = now.replace(
            hour=parsed_time.hour,
            minute=parsed_time.minute,
            second=0,
            microsecond=0
        )

        # Only within the current 24-hour window:
        # if the provided time is later than now, treat it as yesterday.
        if after_dt > now:
            after_dt -= timedelta(days=1)

        return ("time", None, after_dt)

    def __parseTimeString(self, value: str) -> Optional[datetime]:
        value = value.strip().upper()

        patterns = [
            "%I:%M %p",  # 3:15 PM
            "%I %p",     # 3 PM
            "%H:%M",     # 15:15
            "%H",        # 15
        ]

        for fmt in patterns:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        return None

    async def __collectMessages(self, channel: discord.TextChannel, mode: str, count: Optional[int],
                                after_dt: Optional[datetime], interaction: discord.Interaction) -> List[discord.Message]:
        messages: List[discord.Message] = []

        # Get the last N messages
        if mode == "count":
            limit = count if count is not None else 0

            async for msg in channel.history(limit=limit + 50, oldest_first=False):
                # Skip bot messages
                if msg.author.bot:
                    continue

                # Skip interaction message if present
                if interaction.message is not None and msg.id == interaction.message.id:
                    continue

                messages.append(msg)

                if len(messages) >= limit:
                    break

            messages.reverse()
            return messages

        # Get messages within a time window
        if mode == "time":
            if after_dt is None:
                return []

            async for msg in channel.history(
                limit=CommandSummarize.__MESSAGES_COUNT_MAX + 50,
                after=after_dt,
                oldest_first=True
            ):
                # Skip bot messages
                if msg.author.bot:
                    continue

                # Skip interaction message if present
                if interaction.message is not None and msg.id == interaction.message.id:
                    continue

                messages.append(msg)

                # Optional: enforce hard cap here too
                if len(messages) >= CommandSummarize.__MESSAGES_COUNT_MAX:
                    break

            return messages

        return []

    async def __summarizeMessages(self, messages: List[discord.Message]) -> Optional[str]:
        conversation_text = self.__formatMessages(messages)

        # Protect against very large channels by chunking the content.
        text_chunks = self.__chunkText(conversation_text, CommandSummarize.__MESSAGE_CHUNK_MAX)

        partial_summaries: List[str] = []
        for chunk in text_chunks:
            partial_summary = self.__callOpenAISummary(
                prompt=(
                    "Summarize the following Discord channel messages.\n"
                    "Focus on main topics\n\n"
                    f"{chunk}"
                )
            )
            if partial_summary:
                partial_summaries.append(partial_summary)

        if not partial_summaries:
            return None

        if len(partial_summaries) == 1:
            return partial_summaries[0]

        combined = "\n\n".join(
            [f"Partial Summary {i + 1}:\n{s}" for i, s in enumerate(partial_summaries)]
        )

        final_summary = self.__callOpenAISummary(
            prompt=(
                "Combine the following partial summaries into one cohesive summary using bullet points. "
                "Each bullet point can be a few sentences long, or longer if necessary. "
                "There can be up to 5 bullet points max, if there would be more, drop the less \"impactful\" bullet points. "
                "Avoid repeating information and keep the flow natural.\n\n"
                f"{combined}"
            )
        )
        return final_summary

    def __callOpenAISummary(self, prompt: str) -> Optional[str]:
        if self.client is None:
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You summarize Discord conversations clearly and accurately. "
                            "Do not invent facts. Keep summaries readable and well structured."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
            )

            if not response.choices:
                return None

            msg = response.choices[0].message
            if msg is None or msg.content is None:
                return None

            return msg.content.strip()

        except Exception as e:
            CommandSummarize.__LOGGER.log(LogLevel.LEVEL_ERROR, f"OpenAI summarize request failed: {e}")
            return None

    def __formatMessages(self, messages: List[discord.Message]) -> str:
        lines: List[str] = []

        for msg in messages:
            created = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            author = msg.author.display_name if msg.author else "Unknown User"
            content = msg.content.strip()

            if not content and msg.attachments:
                content = "[Attachment only message]"
            elif not content:
                content = "[No text content]"

            attachment_text = ""
            if msg.attachments:
                filenames = ", ".join([a.filename for a in msg.attachments])
                attachment_text = f" Attachments: {filenames}"

            lines.append(f"[{created}] {author}: {content}{attachment_text}")

        return "\n".join(lines)

    def __chunkText(self, text: str, max_chars: int) -> List[str]:
        if len(text) <= max_chars:
            return [text]

        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for line in text.splitlines(keepends=True):
            if current_len + len(line) > max_chars and current:
                chunks.append("".join(current))
                current = [line]
                current_len = len(line)
            else:
                current.append(line)
                current_len += len(line)

        if current:
            chunks.append("".join(current))

        return chunks

    def __splitForDiscord(self, text: str, max_len: int) -> List[str]:
        if len(text) <= max_len:
            return [text]

        parts: List[str] = []
        remaining = text

        while len(remaining) > max_len:
            split_idx = remaining.rfind("\n", 0, max_len)
            if split_idx == -1:
                split_idx = max_len
            parts.append(remaining[:split_idx])
            remaining = remaining[split_idx:].lstrip("\n")

        if remaining:
            parts.append(remaining)

        return parts


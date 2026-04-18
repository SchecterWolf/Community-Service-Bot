__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord

from openai import OpenAI
from typing import Optional

from .ICommand import ICommand

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from core.DB import DB
from core.AIClient import AIClient

class CommandPercy(ICommand):
    __LOGGER = ClassLogger(__name__)
    __MODEL = "gpt-4o-mini"

    def __init__(self):
        super().__init__()

        self.client: Optional[OpenAI] = None
        self.model = CommandPercy.__MODEL
        self.allowedGuild = DB(0).getConfigAttr(GLOBALVARS.CONFIG_PERCY, int, 0)

        self.command = discord.app_commands.Command(
            name="percy",
            description="Blame Percy for something",
            callback=self.generate,
        )
        self.command.error(CommandPercy.generateError)

    def setupCommands(self, tree: discord.app_commands.CommandTree):
        CommandPercy.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Initializing the percy command.")

        self.client = AIClient().getClient()

        # Add the command to the tree
        tree.add_command(self.command)

    def _build_prompt(self, style: str | None = None) -> str:
        prompt = """
Come up with ONE darkly funny, savage sentence that clearly blames a person named Percy for something.

The sentence may or may not start with “it’s Percy’s fault,” but the overall message must clearly imply that Percy is responsible.

The humor should have a dark, cynical, or slightly unhinged tone. It can include adult themes (dating disasters, bad decisions, awkward tension, nightlife, etc.), common life annoyances, petty frustrations, or chaotic scenarios like GTA FiveM RP situations.

You may also incorporate:
- Common everyday frustrations (work, traffic, bad nights out)
- Social awkwardness or embarrassing situations
- Savage jabs at the United Kingdom (e.g., gloomy weather, bland food, awkward culture)
- Chaotic or poorly-run roleplay scenarios (e.g., cops abusing power, scuffed RP moments, etc.)

Percy should come across as deeply incompetent, socially painful to be around, overconfident in the worst way, or the human equivalent of things going wrong.

The joke should feel sharp, dark, and brutally honest — like something you'd say when you're tired, annoyed, and slightly unhinged.

Avoid graphic or explicit sexual content, but suggestive or adult humor is allowed.

Keep it as ONE strong, cutting sentence.

Examples:
- The whole night went downhill the moment Percy said he had a “plan.”
- Somehow Percy turned a simple situation into something that needs therapy to unpack.
- You can always tell Percy was involved by how quickly things stop making sense.
- The FiveM server didn’t stand a chance once Percy decided to get creative.
        """

        if style:
            prompt += f"\nWrite it {style}.\n"

        prompt += "\nNow generate ONE new unique sentence:\n"

        return prompt

    @discord.app_commands.checks.cooldown(5, 60.0, key=lambda i: "global")
    @discord.app_commands.describe(style="(Optional) Style suggestion for the AI generation")
    async def generate(self, interaction: discord.Interaction, style: str | None = None):
        if interaction.guild_id != self.allowedGuild:
            await interaction.response.send_message("This command is not available for this server.", ephemeral=True)
            return

        CommandPercy.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"User {interaction.user.name} called the blame percy command.")

        prompt = self._build_prompt(style)
        response = ""

        await interaction.response.defer(thinking=True, ephemeral=False)

        try:
            if self.client:
                response = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                    max_output_tokens=200,
                )
                response = response.output_text.strip()
        except Exception as e:
            CommandPercy.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Failed to blame percy: {e}")
            response = ""

        if response:
            await interaction.followup.send(response, ephemeral=False)
        else:
            await interaction.followup.send("Could not complete request.", ephemeral=True)

    async def generateError(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Slow down, give Percy a break! Try again in {error.retry_after:.1f} seconds.",
                ephemeral=True,
            )
            return

        CommandPercy.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Unhandled Percy command error: {error}")


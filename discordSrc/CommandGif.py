__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import asyncio
import discord
import io
import random
import re
import shutil
import string
import subprocess
import tempfile

from .Decorators import verifyIsListRoles
from .ICommand import ICommand

from config.ClassLogger import ClassLogger, LogLevel

from typing import List, Optional
from yt_dlp import YoutubeDL

class CommandGif(ICommand):
    __LOGGING = ClassLogger(__name__)
    __FFMPEG = "ffmpeg"
    __DEFAULT_DURATION = 5.0
    __MAX_DURATION = 15.0
    __MAX_DURATION_VID = 600 # Max 10 minute vid
    __MAX_FPS = 12
    __WIDTH = 360
    __WIDTH_MP4 = 720
    __WIDTH_MP4_LOW = 480

    def __init__(self):
        super().__init__()

        self.commands: List[discord.app_commands.Command] = [
            discord.app_commands.Command(
                name="gif",
                description="Make a gif from a youtube video or clip",
                callback=self.makeGif
            ),
            discord.app_commands.Command(
                name="vid",
                description="Make a MP4 video from a youtube video or clip",
                callback=self.makeVid
            )
        ]

    def setupCommands(self, tree: discord.app_commands.CommandTree):
        if shutil.which(CommandGif.__FFMPEG) is None:
            CommandGif.__LOGGING.log(LogLevel.LEVEL_ERROR, "ffmpeg not found on PATH, skipping adding the GIF command.")
        else:
            CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, "Initializing the GIF command.")
            for command in self.commands:
                tree.add_command(command)

    async def makeGif(self, interaction: discord.Interaction, url: str, timestamp: str = "0", duration: float = __DEFAULT_DURATION):
        return await self.makeMedia(True, interaction, url, timestamp, duration)

    @discord.app_commands.describe(url="Youtube URL clip")
    @discord.app_commands.describe(start_timestamp="Starting timestamp [format SS, MM:SS, HH:MM:SS]")
    @discord.app_commands.describe(end_timestamp="Ending timestamp [format SS, MM:SS, HH:MM:SS]")
    async def makeVid(self, interaction: discord.Interaction, url: str, start_timestamp: str = "0", end_timestamp: str = "0"):
        start_sec = self._parse_time_to_seconds(start_timestamp)
        end_sec = self._parse_time_to_seconds(end_timestamp)

        # Validate times
        if end_sec <= start_sec or end_sec - start_sec == 0:
            await interaction.response.send_message("\U0000274C end_timestamp must be greater than timestamp!")
            return

        return await self.makeMedia(False, interaction, url, start_timestamp, end_sec - start_sec)

    async def makeMedia(self, makeGif: bool, interaction: discord.Interaction, url: str, timestamp: str = "0", duration: float = __DEFAULT_DURATION):
        if not await verifyIsListRoles(interaction, "SeniorRoles", "\U0000274C You're not a high enough rank to use this feature."):
            return
        elif makeGif and (duration < 0 or duration > CommandGif.__MAX_DURATION):
            await interaction.response.send_message(f"\U0000274C duration can't be longer than {CommandGif.__MAX_DURATION} seconds!")
            return
        elif not makeGif and duration > CommandGif.__MAX_DURATION_VID:
            await interaction.response.send_message(f"\U0000274C duration can't be longer than {CommandGif.__MAX_DURATION_VID} seconds!")
            return

        CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, f"Make GIF command called by user {interaction.user.display_name}")

        await interaction.response.defer(thinking=True)
        info = await asyncio.to_thread(self.__extractVideoInfo, url)
        if info.get("is_live") or info.get("live_status") == "is_live":
            await interaction.followup.send(f"\U0000274C You must wait for the livestream to end in order to use this command (because youtube is weird like that)!")
            return

        filename = interaction.user.name + ''.join(random.choices(string.digits, k=8)) + f".{'gif' if makeGif else 'mp4'}"

        try:
            if self.__isClip(url):
                gifFile = await self.__makeFromClip(makeGif, info, filename)
            else:
                gifFile = await self.__makeFromVid(makeGif, info, timestamp, duration, filename)

            if not gifFile:
                raise Exception("Could not generate")
            else:
                await interaction.followup.send(file=gifFile)

        except Exception as e:
            CommandGif.__LOGGING.log(LogLevel.LEVEL_ERROR, f"GIF command failed: {str(e)}")
            mediaType = "GIF" if makeGif else "MP4"
            await interaction.followup.send(f"Failed to generate {mediaType}: {str(e)}")

    def __isClip(self, url: str) -> bool:
        if not isinstance(url, str):
            return False

        return bool(re.search(r"(youtube\.com|youtu\.be)/clip/", url))

    async def __makeFromVid(self, makeGif: bool, info: dict, start_time: str, duration: float, filename: Optional[str] = None) -> discord.File:
        CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, "Media url is a video.")

        fmt = self.__pickVideoFormat(info, duration)
        media_url = fmt["url"]
        startSeconds = self._parse_time_to_seconds(start_time)
        if makeGif:
            fileBytes = await self.__renderGifBytes(media_url, startSeconds, duration)
        else:
            audio_fmt = self.__pickAudioFormat(info)
            audio_url = audio_fmt["url"] if audio_fmt else None
            fileBytes = await self.__renderMp4Bytes(media_url, startSeconds, duration, audio_url)
            sizeMB = len(fileBytes) / (1024 * 1024)
            CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, f"Generated MP4 size: {sizeMB:.2f} MB")

        safe_title = self.__sanitizeFilename(info.get("title") or "clip")
        out_name = filename or f"{safe_title}.{'gif' if makeGif else 'mp4'}"
        return discord.File(io.BytesIO(fileBytes), filename=out_name)

    async def __makeFromClip(self, makeGif: bool, info: dict, filename: Optional[str] = None) -> discord.File:
        CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, "Media url is a clip.")

        start_time, duration = self.__extractClipRange(info)
        if duration <= 0:
            raise ValueError("Could not determine clip duration from the YouTube clip URL.")
        if duration > CommandGif.__MAX_DURATION:
            raise ValueError(
                f"Clip duration is {duration:.2f}s, which exceeds the max allowed "
                f"duration of {CommandGif.__MAX_DURATION:.2f}s."
            )

        fmt = self.__pickVideoFormat(info)
        media_url = fmt["url"]
        if makeGif:
            fileBytes = await self.__renderGifBytes(media_url, start_time, duration)
        else:
            audio_fmt = self.__pickAudioFormat(info)
            audio_url = audio_fmt["url"] if audio_fmt else None
            fileBytes = await self.__renderMp4Bytes(media_url, start_time, duration, audio_url)

        clip_title = (
            info.get("clip_title")
            or info.get("section_title")
            or info.get("title")
            or "clip"
        )
        safe_title = self.__sanitizeFilename(clip_title)
        out_name = filename or f"{safe_title}.{'gif' if makeGif else 'mp4'}"

        return discord.File(io.BytesIO(fileBytes), filename=out_name)

    def __extractVideoInfo(self, url: str) -> dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4/best",
        }

        with YoutubeDL(ydl_opts) as ydl:
            ret = ydl.extract_info(url, download=False)
            if not isinstance(ret, dict):
                raise ValueError("Extracted youtube info was the incorrect format.")
            return ret

    def __pickVideoFormat(self, info: dict, duration: float = 0.0) -> dict:
        formats = info.get("formats") or []
        suggestedResolution = CommandGif.__WIDTH_MP4 if duration < 300.0 else CommandGif.__WIDTH_MP4_LOW

        CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, f"Using resolution: {suggestedResolution}")

        video_formats = [
            f for f in formats
            if f.get("vcodec") not in (None, "none") and f.get("url")
        ]

        if not video_formats:
            if info.get("url"):
                return info
            raise RuntimeError("Could not find a usable video format")

        def url_of(f: dict) -> str:
            return str(f.get("url") or "")

        def manifest_url_of(f: dict) -> str:
            return str(f.get("manifest_url") or "")

        def protocol_of(f: dict) -> str:
            return str(f.get("protocol") or "")

        def is_dash_manifest(f: dict) -> bool:
            url = url_of(f)
            manifest_url = manifest_url_of(f)
            protocol = protocol_of(f)

            return (
                "http_dash_segments" in protocol
                or "/api/manifest/dash/" in url
                or "/api/manifest/dash/" in manifest_url
            )

        def is_hls_playlist(f: dict) -> bool:
            url = url_of(f)
            manifest_url = manifest_url_of(f)
            protocol = protocol_of(f)

            return (
                protocol in ("m3u8", "m3u8_native")
                or "m3u8" in protocol
                or "/api/manifest/hls_playlist/" in url
                or "/api/manifest/hls_playlist/" in manifest_url
                or url.endswith(".m3u8")
                or manifest_url.endswith(".m3u8")
            )

        def is_direct_media(f: dict) -> bool:
            url = url_of(f)
            protocol = protocol_of(f)

            # direct-ish playable media URLs; not a YouTube manifest wrapper
            return (
                not is_dash_manifest(f)
                and not is_hls_playlist(f)
                and protocol not in ("http_dash_segments",)
                and "/api/manifest/" not in url
            )

        def height(f: dict) -> int:
            return int(f.get("height") or 0)

        def tbr(f: dict) -> int:
            return int(f.get("tbr") or 0)

        def fps(f: dict) -> int:
            return int(f.get("fps") or 0)

        def quality_score(f: dict) -> tuple[int, int]:
            return (tbr(f), fps(f))

        def pick_by_resolution(candidates: list[dict]) -> dict:
            exact_720 = [f for f in candidates if height(f) == suggestedResolution]
            if exact_720:
                return max(exact_720, key=quality_score)

            above_720 = [f for f in candidates if height(f) > suggestedResolution]
            if above_720:
                return min(
                    above_720,
                    key=lambda f: (
                        height(f),
                        -tbr(f),
                        -fps(f),
                    ),
                )

            below_720 = [f for f in candidates if height(f) < suggestedResolution]
            if below_720:
                return max(
                    below_720,
                    key=lambda f: (
                        height(f),
                        tbr(f),
                        fps(f),
                    ),
                )

            raise RuntimeError("Could not find a usable video format")

        # Tier 1: direct media URLs
        direct_candidates = [f for f in video_formats if is_direct_media(f)]
        if direct_candidates:
            return pick_by_resolution(direct_candidates)

        # Tier 2: HLS playlists
        hls_candidates = [f for f in video_formats if is_hls_playlist(f)]
        if hls_candidates:
            return pick_by_resolution(hls_candidates)

        # Tier 3: anything except DASH manifests
        non_dash_candidates = [f for f in video_formats if not is_dash_manifest(f)]
        if non_dash_candidates:
            return pick_by_resolution(non_dash_candidates)

        # Last resort: everything
        return pick_by_resolution(video_formats)

    def __extractClipRange(self, info: dict) -> tuple[float, float]:
        start = info.get("start_time")
        end = info.get("end_time")
        if start is not None and end is not None:
            start = float(start)
            end = float(end)
            return start, max(0.0, end - start)

        duration = info.get("duration")
        if start is not None and duration is not None:
            return float(start), float(duration)

        section_start = info.get("section_start")
        section_end = info.get("section_end")
        if section_start is not None and section_end is not None:
            section_start = float(section_start)
            section_end = float(section_end)
            return section_start, max(0.0, section_end - section_start)

        requested_downloads = info.get("requested_downloads") or []
        for entry in requested_downloads:
            s = entry.get("section_start")
            e = entry.get("section_end")
            if s is not None and e is not None:
                s = float(s)
                e = float(e)
                return s, max(0.0, e - s)

        raise ValueError("This clip URL did not expose a usable start/end time.")

    async def __renderGifBytes(self, media_url: str, start_time: float, duration: float) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            palette_path = f"{tmp}/palette.png"
            gif_path = f"{tmp}/out.gif"

            base_filter = (
                f"fps={CommandGif.__MAX_FPS},"
                f"scale={CommandGif.__WIDTH}:-2:flags=lanczos"
            )

            palette_cmd = [
                CommandGif.__FFMPEG,
                "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", media_url,
                "-vf",
                f"{base_filter},palettegen=stats_mode=full",
                palette_path,
            ]

            gif_cmd = [
                CommandGif.__FFMPEG,
                "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", media_url,
                "-i", palette_path,
                "-filter_complex",
                #f"{base_filter}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
                f"{base_filter}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
                gif_path,
            ]

            result = await asyncio.to_thread(
                subprocess.run,
                palette_cmd,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError("Video is unavailable, try again later")

            result = await asyncio.to_thread(
                subprocess.run,
                gif_cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError("Video is unavailable, try again later")

            with open(gif_path, "rb") as f:
                return f.read()

    async def __renderMp4Bytes(self, media_url: str, start_time: float, duration: float, audio_url: Optional[str] = None) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            mp4_path = f"{tmp}/out.mp4"

            mp4_cmd = [
                CommandGif.__FFMPEG,
                "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", media_url,
            ]

            if audio_url:
                mp4_cmd.extend([
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-i", audio_url,
                ])

            mp4_cmd.extend([
                "-c:v", "copy",
            ])

            if audio_url:
                mp4_cmd.extend([
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-shortest",
                ])
            else:
                mp4_cmd.append("-an")

            mp4_cmd.extend([
                "-movflags", "+faststart",
                mp4_path,
            ])

            CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, f"Running download command: {mp4_cmd}")
            await asyncio.to_thread(
                subprocess.run,
                mp4_cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            CommandGif.__LOGGING.log(LogLevel.LEVEL_DEBUG, "Download complete.")

            with open(mp4_path, "rb") as f:
                return f.read()

    def __sanitizeFilename(self, text: str) -> str:
        return re.sub(r'[^\w\-_. ]', "", text).strip()[:80] or "clip"

    def _parse_time_to_seconds(self, value: str) -> float:
        """
        Accepts ONLY string formats:
        - "90"
        - "1:30"
        - "01:02:30"
        """

        if not isinstance(value, str):
            raise ValueError("start_time must be a string")

        value = value.strip()

        if not value:
            raise ValueError("start_time cannot be empty")

        # Case: "90"
        if value.isdigit():
            return float(value)

        parts = value.split(":")

        try:
            if len(parts) == 2:
                # MM:SS
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)

            elif len(parts) == 3:
                # HH:MM:SS
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + int(seconds)

        except ValueError:
            raise ValueError("Time components must be integers")

        raise ValueError(
            "Invalid time format. Use 'SS', 'MM:SS', or 'HH:MM:SS'"
        )

    def __pickAudioFormat(self, info: dict) -> Optional[dict]:
        formats = info.get("formats") or []

        audio_formats = [
            f for f in formats
            if f.get("acodec") not in (None, "none") and f.get("url")
        ]

        if not audio_formats:
            if info.get("url") and info.get("acodec") not in (None, "none"):
                return info
            return None

        def abr(f: dict) -> float:
            return float(f.get("abr") or 0)

        def is_direct_audio(f: dict) -> bool:
            protocol = str(f.get("protocol") or "")
            url = str(f.get("url") or "")
            return (
                "http_dash_segments" not in protocol
                and "/api/manifest/" not in url
            )

        direct = [f for f in audio_formats if is_direct_audio(f)]
        if direct:
            return max(direct, key=abr)

        return max(audio_formats, key=abr)


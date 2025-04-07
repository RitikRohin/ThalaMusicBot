import os
import re
import asyncio
import aiohttp
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
import yt_dlp

from EsproMusic.utils.database import is_on_off
from EsproMusic.utils.formatters import time_to_seconds

API_KEY = os.getenv("AIzaSyB0Dd46e_EwagTplRuEIo1uAiVtVDfND3c")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            text = message.text or message.caption or ""
            entities = message.entities or message.caption_entities or []
            for entity in entities:
                if entity.type in [MessageEntityType.URL, MessageEntityType.TEXT_LINK]:
                    return entity.url or text[entity.offset: entity.offset + entity.length]
        return None

    async def fetch_video_details(self, video_id):
        url = f"{YOUTUBE_API_URL}/videos?part=snippet,contentDetails&id={video_id}&key={API_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        if not data["items"]:
            return None
        video = data["items"][0]
        title = video["snippet"]["title"]
        duration = video["contentDetails"]["duration"]
        thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
        return title, duration, thumbnail, video_id

    def parse_iso_duration(self, duration):
        import isodate
        try:
            duration_obj = isodate.parse_duration(duration)
            total_seconds = int(duration_obj.total_seconds())
            minutes = f"{total_seconds // 60}:{total_seconds % 60:02d}"
            return minutes, total_seconds
        except:
            return "0:00", 0

    async def details(self, link: str, videoid: Union[bool, str] = None):
        video_id = link if videoid else self.extract_video_id(link)
        title, duration_iso, thumbnail, vidid = await self.fetch_video_details(video_id)
        duration_min, duration_sec = self.parse_iso_duration(duration_iso)
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        title, *_ = await self.details(link, videoid)
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        _, duration_min, *_ = await self.details(link, videoid)
        return duration_min

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        *_, thumbnail, _ = await self.details(link, videoid)
        return thumbnail

    def extract_video_id(self, link):
        import urllib.parse
        if "youtu.be" in link:
            return link.split("/")[-1]
        query = urllib.parse.urlparse(link).query
        return urllib.parse.parse_qs(query).get("v", [""])[0]

    async def track(self, link: str, videoid: Union[bool, str] = None):
        title, duration_min, _, thumbnail, vidid = await self.details(link, videoid)
        return {
            "title": title,
            "link": f"{self.base}{vidid}",
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }, vidid

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, stderr.decode())

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        return [vid for vid in playlist.split("\n") if vid]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        ydl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        with ydl:
            r = ydl.extract_info(link, download=False)
            formats = [
                {
                    "format": f["format"],
                    "filesize": f.get("filesize"),
                    "format_id": f["format_id"],
                    "ext": f["ext"],
                    "format_note": f.get("format_note"),
                    "yturl": link,
                }
                for f in r["formats"]
                if "dash" not in str(f.get("format", "")).lower()
            ]
        return formats, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        query = link if not videoid else self.base + link
        url = f"{YOUTUBE_API_URL}/search?part=snippet&type=video&maxResults=10&q={query}&key={API_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        result = data["items"][query_type]
        video_id = result["id"]["videoId"]
        snippet = result["snippet"]
        title = snippet["title"]
        thumbnail = snippet["thumbnails"]["high"]["url"]
        # Get duration via details
        _, duration, *_ = await self.details(video_id, True)
        return title, duration, thumbnail, video_id

    async def download(self, link: str, mystic, video=False, videoid=None,
                       songaudio=False, songvideo=False, format_id=None, title=None):
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl():
            opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(opts)
            info = x.extract_info(link, False)
            file = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(file): return file
            x.download([link])
            return file

        def video_dl():
            opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(opts)
            info = x.extract_info(link, False)
            file = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(file): return file
            x.download([link])
            return file

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            opts = {
                "format": format_id,
                "outtmpl": fpath,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            yt_dlp.YoutubeDL(opts).download([link])

        def song_video_dl():
            fpath = f"downloads/{title}"
            opts = {
                "format": f"{format_id}+140",
                "outtmpl": fpath,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
            }
            yt_dlp.YoutubeDL(opts).download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            return f"downloads/{title}.mp4"
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            return f"downloads/{title}.mp3"
        elif video:
            if await is_on_off(1):
                return await loop.run_in_executor(None, video_dl), True
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", link,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                return stdout.decode().split("\n")[0], None
        else:
            return await loop.run_in_executor(None, audio_dl), True


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return out.decode() if out else err.decode()

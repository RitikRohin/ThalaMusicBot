import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build
from EsproMusic.utils.database import is_on_off
from EsproMusic.utils.formatters import time_to_seconds


YOUTUBE_API_KEY = "AIzaSyB0Dd46e_EwagTplRuEIo1uAiVtVDfND3c"  # Replace this with your actual key
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return re.search(self.regex, link) is not None

    async def url(self, message: Message) -> Union[str, None]:
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)

        for msg in messages:
            entities = msg.entities or msg.caption_entities or []
            for entity in entities:
                if entity.type in (MessageEntityType.URL, MessageEntityType.TEXT_LINK):
                    return entity.url if entity.type == MessageEntityType.TEXT_LINK else (msg.text or msg.caption)[entity.offset:entity.offset + entity.length]
        return None

    async def search(self, query, limit=1):
        response = youtube.search().list(
            q=query, part="snippet", type="video", maxResults=limit
        ).execute()
        return response.get("items", [])

    async def details(self, video_id: str):
        video_id = video_id.replace("https://www.youtube.com/watch?v=", "").split("&")[0]
        response = youtube.videos().list(
            id=video_id,
            part="snippet,contentDetails"
        ).execute()

        item = response["items"][0]
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        duration_iso = item["contentDetails"]["duration"]
        duration_sec = time_to_seconds(duration_iso)
        return title, duration_iso, duration_sec, thumbnail, video_id

    async def video(self, link: str):
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        return 0, stderr.decode()

    async def download(self, link, mystic, video=False, songaudio=False, songvideo=False, format_id=None, title=None):
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.{info['ext']}")

        def video_dl():
            ydl_opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.{info['ext']}")

        if songvideo:
            return await loop.run_in_executor(None, video_dl)
        elif songaudio:
            return await loop.run_in_executor(None, audio_dl)
        elif video:
            if await is_on_off(1):
                return await loop.run_in_executor(None, video_dl)
            else:
                code, result = await self.video(link)
                if code == 1:
                    return result
                return None
        else:
            return await loop.run_in_executor(None, audio_dl)

    async def playlist(self, playlist_id: str, max_videos: int = 10):
        videos = []
        next_page_token = None
        while len(videos) < max_videos:
            response = youtube.playlistItems().list(
                playlistId=playlist_id,
                part="contentDetails",
                maxResults=min(50, max_videos - len(videos)),
                pageToken=next_page_token,
            ).execute()
            videos.extend([item["contentDetails"]["videoId"] for item in response["items"]])
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        return videos

import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
import isodate

from EsproMusic import app
from config import YOUTUBE_IMG_URL, YT_API_KEY


def changeImageSize(maxWidth, maxHeight, image):
    ratio = min(maxWidth / image.width, maxHeight / image.height)
    return image.resize((int(image.width * ratio), int(image.height * ratio)))


def clear(text):
    title = ""
    for word in text.split():
        if len(title + " " + word) < 60:
            title += " " + word
    return title.strip()


async def get_video_info(videoid):
    url = (
        f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics"
        f"&id={videoid}&key={YT_API_KEY}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            items = data.get("items")
            if not items:
                return None
            info = items[0]
            snippet = info["snippet"]
            stats = info.get("statistics", {})
            duration = info["contentDetails"]["duration"]

            # Convert ISO 8601 duration to mm:ss format
            dur = isodate.parse_duration(duration)
            duration_str = f"{dur.seconds // 60:02}:{dur.seconds % 60:02}"

            return {
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "views": stats.get("viewCount", "N/A"),
                "thumbnail": snippet["thumbnails"]["high"]["url"],
                "duration": duration_str,
            }


async def get_thumb(videoid):
    final_path = f"cache/{videoid}.png"
    if os.path.exists(final_path):
        return final_path

    video_info = await get_video_info(videoid)
    if not video_info:
        return YOUTUBE_IMG_URL

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_info["thumbnail"]) as resp:
                if resp.status == 200:
                    temp_path = f"cache/thumb{videoid}.png"
                    async with aiofiles.open(temp_path, mode="wb") as f:
                        await f.write(await resp.read())

        youtube = Image.open(temp_path)
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")
        background = ImageEnhance.Brightness(
            image2.filter(ImageFilter.BoxBlur(10))
        ).enhance(0.5)

        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype("EsproMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("EsproMusic/assets/font.ttf", 30)

        # Add text info
        draw.text((1110, 8), unidecode(app.name), fill="white", font=arial)
        draw.text((55, 560), f"{video_info['channel']} | {video_info['views']}", fill="white", font=arial)
        draw.text((57, 60), clear(video_info["title"]), fill="white", font=font)
        draw.line([(55, 660), (1220, 660)], fill="white", width=5)
        draw.ellipse([(918, 648), (942, 672)], outline="white", fill="white", width=15)
        draw.text((36, 685), "00:00", fill="white", font=arial)
        draw.text((1185, 685), video_info["duration"], fill="white", font=arial)

        # Centered circular cropped thumbnail with white border
        thumb_crop = image1.copy().resize((250, 250))
        mask = Image.new("L", (250, 250), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 250, 250), fill=255)

        border_size = 10
        bordered_thumb = Image.new("RGBA", (270, 270), (255, 255, 255, 0))
        border_draw = ImageDraw.Draw(bordered_thumb)
        border_draw.ellipse((0, 0, 270, 270), fill=(255, 255, 255, 255))
        bordered_thumb.paste(thumb_crop, (10, 10), mask)

        center_x = (1280 - 270) // 2
        center_y = (720 - 270) // 2
        background.paste(bordered_thumb, (center_x, center_y), bordered_thumb)

        # Final save
        os.remove(temp_path)
        background.save(final_path)
        return final_path

    except Exception as e:
        print(f"Thumbnail creation failed: {e}")
        return YOUTUBE_IMG_URL

import asyncio
import os
import random
import re
import aiofiles
import aiohttp
from PIL import Image, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL


def make_col():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


def truncate(text):
    words = text.split(" ")
    text1 = ""
    text2 = ""
    for word in words:
        if len(text1) + len(word) < 30:
            text1 += " " + word
        elif len(text2) + len(word) < 30:
            text2 += " " + word
    return [text1.strip(), text2.strip()]


async def get_thumb(videoid):
    try:
        final_path = f"cache/{videoid}.jpg"
        if os.path.isfile(final_path):
            return final_path

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            try:
                title = re.sub(r"\W+", " ", result.get("title", "Unsupported Title")).title()
            except:
                title = "Unsupported Title"
            duration = result.get("duration", "Unknown Mins")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            views = result.get("viewCount", {}).get("short", "Unknown Views")
            channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Download YouTube thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg") as resp:
                if resp.status == 200:
                    async with aiofiles.open(f"cache/thumb{videoid}.jpg", mode="wb") as f:
                        await f.write(await resp.read())

        # Load and resize the thumbnail
        youtube = Image.open(f"cache/thumb{videoid}.jpg")
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")

        # Create blurred background
        background = image2.filter(filter=ImageFilter.BoxBlur(30))
        enhancer = ImageEnhance.Brightness(background)
        image2 = enhancer.enhance(0.6)

        # Crop center thumbnail and resize
        image3 = image1.crop((280, 0, 1000, 720))
        image3 = image3.resize((480, 270))  # Resize thumbnail

        # Create white border
        border_width = 10
        bg_width = image3.width + 2 * border_width
        bg_height = image3.height + 2 * border_width
        white_bg = Image.new("RGB", (bg_width, bg_height), (255, 255, 255))
        white_bg.paste(image3, (border_width, border_width))

        # Paste bordered thumbnail centered on background
        image2 = image2.convert("RGB")
        bg_w, bg_h = image2.size
        thumb_w, thumb_h = white_bg.size
        x = (bg_w - thumb_w) // 2
        y = (bg_h - thumb_h) // 2
        image2.paste(white_bg, (x, y))

        # Fonts (optional if you want to add text later)
        font1 = ImageFont.truetype('EsproMusic/assets/font.ttf', 30)
        font2 = ImageFont.truetype('EsproMusic/assets/font2.ttf', 70)
        font3 = ImageFont.truetype('EsproMusic/assets/font2.ttf', 40)

        # Save and return
        image2.save(final_path)
        return final_path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL

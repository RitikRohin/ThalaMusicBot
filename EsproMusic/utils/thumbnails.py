import asyncio
import os
import random
import re
import textwrap
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch
import numpy as np
from config import YOUTUBE_IMG_URL


def make_col():
    return (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


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
        cached_file = f"cache/{videoid}.jpg"
        if os.path.isfile(cached_file):
            return cached_file

        # Get video details
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        for result in (await results.next())["result"]:
            title = re.sub(r"\W+", " ", result.get("title", "Unsupported Title")).title()
            duration = result.get("duration", "Unknown Mins")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            views = result.get("viewCount", {}).get("short", "Unknown Views")
            channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg") as resp:
                if resp.status == 200:
                    async with aiofiles.open(f"cache/thumb{videoid}.jpg", mode="wb") as f:
                        await f.write(await resp.read())

        # Prepare background
        youtube = Image.open(f"cache/thumb{videoid}.jpg")
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")
        background = image2.filter(ImageFilter.BoxBlur(30))
        background = ImageEnhance.Brightness(background).enhance(0.6)
        image2 = background

        # Load and color circle
        circle = Image.open("EsproMusic/assets/circle.png").convert("RGBA")
        color = make_col()
        data = np.array(circle)
        red, green, blue, alpha = data.T
        white_areas = (red == 255) & (green == 255) & (blue == 255)
        data[..., :-1][white_areas.T] = color
        circle = Image.fromarray(data)

        # Crop center image circle
        image3 = image1.crop((280, 0, 1000, 720))
        lum_img = Image.new("L", [720, 720], 0)
        ImageDraw.Draw(lum_img).pieslice([(0, 0), (720, 720)], 0, 360, fill=255, outline="white")
        final_img_arr = np.dstack((np.array(image3), np.array(lum_img)))
        image3 = Image.fromarray(final_img_arr).resize((600, 600))

        # Paste image parts
        image2.paste(image3, (50, 70), mask=image3)
        image2.paste(circle, (0, 0), mask=circle)

        # Fonts
        font1 = ImageFont.truetype('EsproMusic/assets/font.ttf', 30)
        font2 = ImageFont.truetype('EsproMusic/assets/font2.ttf', 70)
        font3 = ImageFont.truetype('EsproMusic/assets/font2.ttf', 40)
        font4 = ImageFont.truetype('EsproMusic/assets/font2.ttf', 35)

        # Draw text
        draw = ImageDraw.Draw(image2)
        draw.text((10, 10), "ESPRO MUSIC", fill="white", font=font1)
        draw.text((670, 150), "NOW PLAYING", fill="white", font=font2, stroke_width=2, stroke_fill="white")

        title1 = truncate(title)
        draw.text((670, 300), title1[0], fill="white", stroke_width=1, stroke_fill="white", font=font3)
        draw.text((670, 350), title1[1], fill="white", stroke_width=1, stroke_fill="white", font=font3)

        draw.text((670, 450), f"Views : {views}", fill="white", font=font4)
        draw.text((670, 500), f"Duration : {duration} Mins", fill="white", font=font4)
        draw.text((670, 550), f"Channel : {channel}", fill="white", font=font4)

        # Save final image (no border)
        image2 = image2.convert("RGB")
        image2.save(cached_file)
        return cached_file

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL

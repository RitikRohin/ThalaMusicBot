import asyncio
import os
import random
import aiofiles
import aiohttp
from PIL import Image, ImageEnhance, ImageFilter, ImageFont, ImageDraw
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


async def get_thumb(videoid):
    try:
        final_path = f"cache/{videoid}.jpg"
        if os.path.isfile(final_path):
            return final_path

        # Download YouTube thumbnail with fallback
        async with aiohttp.ClientSession() as session:
            thumb_url = f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    thumb_url = f"http://img.youtube.com/vi/{videoid}/hqdefault.jpg"
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(f"cache/thumb{videoid}.jpg", mode="wb") as f:
                        await f.write(await resp.read())

        # Load and resize the image
        youtube = Image.open(f"cache/thumb{videoid}.jpg")
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")

        # Create blurred background
        background = image2.filter(ImageFilter.BoxBlur(30))
        enhancer = ImageEnhance.Brightness(background)
        image2 = enhancer.enhance(0.6).convert("RGB")

        # Crop and resize thumbnail
        image3 = image1.crop((280, 0, 1000, 720)).resize((854, 480))
        white_bg = Image.new("RGB", (image3.width + 20, image3.height + 20), (255, 255, 255))
        white_bg.paste(image3, (10, 10))

        # Paste on background
        x = (image2.width - white_bg.width) // 2
        y = (image2.height - white_bg.height) // 2
        image2.paste(white_bg, (x, y))

        # Draw text and play button
        draw = ImageDraw.Draw(image2)
        try:
            font_title = ImageFont.truetype("EsproMusic/assets/font2.ttf", 60)
            font_channel = ImageFont.truetype("EsproMusic/assets/font.ttf", 28)
        except:
            font_title = font_channel = ImageFont.load_default()

        # Placeholder info (can be replaced with YouTube Data API values)
        title_text = "Video Title"
        channel_text = "Channel Name"

        # Draw title and channel
        draw.text((40, 580), title_text, font=font_title, fill=(255, 255, 255))
        draw.text((40, 660), f"by {channel_text}", font=font_channel, fill=(200, 200, 200))

        # Draw play button in center
        cx, cy = image2.size[0] // 2, image2.size[1] // 2
        triangle = [
            (cx - 30, cy - 40),
            (cx - 30, cy + 40),
            (cx + 40, cy)
        ]
        draw.polygon(triangle, fill=(255, 255, 255))

        # Save final image
        image2.save(final_path, quality=85)
        return final_path

    except Exception as e:
        print(f"Error in get_thumb: {e}")
        return YOUTUBE_IMG_URL

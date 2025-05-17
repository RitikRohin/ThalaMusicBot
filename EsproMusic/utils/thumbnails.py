import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from EsproMusic import app
from config import YOUTUBE_IMG_URL


def change_image_size(max_width, max_height, image):
    # Resize preserving aspect ratio within max_width & max_height
    width_ratio = max_width / image.size[0]
    height_ratio = max_height / image.size[1]
    scale_factor = min(width_ratio, height_ratio)
    new_width = int(image.size[0] * scale_factor)
    new_height = int(image.size[1] * scale_factor)
    return image.resize((new_width, new_height), Image.LANCZOS)


def truncate_text(text, max_length=60):
    # Truncate title carefully without cutting words abruptly
    words = text.split()
    truncated = ""
    for word in words:
        if len(truncated) + len(word) + 1 <= max_length:
            truncated += (" " if truncated else "") + word
        else:
            break
    return truncated


async def get_thumb(videoid):
    cache_path = f"cache/{videoid}.png"
    if os.path.isfile(cache_path):
        return cache_path

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        response = await results.next()
        video_info = response["result"][0]

        title = video_info.get("title", "Unsupported Title")
        # Clean title text
        title = re.sub(r"\W+", " ", title)
        title = title.title()

        channel = video_info.get("channel", {}).get("name", "Unknown Channel")
        views = video_info.get("viewCount", {}).get("short", "Unknown Views")
        duration = video_info.get("duration", "Unknown Duration")
        thumbnail_url = video_info["thumbnails"][0]["url"].split("?")[0]

        # Download thumbnail image asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                f = await aiofiles.open(f"cache/thumb_{videoid}.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

        base_img = Image.open(f"cache/thumb_{videoid}.png").convert("RGBA")
        base_img = change_image_size(1280, 720, base_img)

        # Create background blur & darken overlay
        background = base_img.filter(ImageFilter.GaussianBlur(radius=15))
        enhancer = ImageEnhance.Brightness(background)
        dark_background = enhancer.enhance(0.35)

        # Create circular mask
        circle_diameter = 400
        circle_radius = circle_diameter // 2

        # Resize base image to fit inside circle
        img_for_circle = change_image_size(circle_diameter, circle_diameter, base_img)

        # Create a mask with a white circle on black background
        mask = Image.new("L", (circle_diameter, circle_diameter), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, circle_diameter, circle_diameter), fill=255)

        # Apply mask to get circular cropped image
        circular_img = Image.new("RGBA", (circle_diameter, circle_diameter), (0,0,0,0))
        circular_img.paste(img_for_circle, (0,0), mask=mask)

        # Paste the circular image at the center of the dark background
        bg_width, bg_height = dark_background.size
        center_x = (bg_width - circle_diameter) // 2
        center_y = (bg_height - circle_diameter) // 2
        dark_background.paste(circular_img, (center_x, center_y), circular_img)

        # Draw a white circular border around the circle
        draw = ImageDraw.Draw(dark_background)
        border_width = 10
        draw.ellipse(
            (center_x - border_width//2, center_y - border_width//2,
             center_x + circle_diameter + border_width//2, center_y + circle_diameter + border_width//2),
            outline=(255, 255, 255, 200),
            width=border_width
        )

        # Load fonts
        font_path_bold = "EsproMusic/assets/font2.ttf"
        font_path_regular = "EsproMusic/assets/font.ttf"
        font_title = ImageFont.truetype(font_path_bold, 60)
        font_info = ImageFont.truetype(font_path_regular, 36)
        font_small = ImageFont.truetype(font_path_regular, 28)

        # Overlay semi-transparent gradient rectangle behind text area to the right of circle
        gradient_height = 250
        gradient_width = 700
        gradient = Image.new("L", (1, gradient_height))
        for y in range(gradient_height):
            opacity = int(255 * (y / gradient_height) * 0.85)
            gradient.putpixel((0, y), opacity)
        alpha_gradient = gradient.resize((gradient_width, gradient_height))

        rectangle = Image.new("RGBA", (gradient_width, gradient_height), (0, 0, 0, 180))
        rect_x = center_x + circle_diameter + 50
        rect_y = center_y + 70
        dark_background.paste(rectangle, (rect_x, rect_y), alpha_gradient)

        # Title text (wrapped truncation)
        final_title = truncate_text(unidecode(title), 70)
        text_x = rect_x + 20
        text_y = rect_y + 10
        draw.text((text_x, text_y), final_title, font=font_title, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 180))

        # Channel | Views info
        info_text = f"{channel} | {views}"
        draw.text((text_x, text_y + 90), info_text, font=font_info, fill=(200, 200, 200), stroke_width=1, stroke_fill=(0, 0, 0, 150))

        # Duration with border rectangle below text area
        duration_box_size = (180, 60)
        duration_pos = (text_x + gradient_width - 200, text_y + 170)
        draw.rectangle([duration_pos, (duration_pos[0] + duration_box_size[0], duration_pos[1] + duration_box_size[1])], fill=(0, 0, 0, 180), outline=(255,255,255), width=3)
        draw.text((duration_pos[0] + 35, duration_pos[1] + 15), duration, font=font_info, fill=(255, 255, 255))

        # Draw bottom progress bar line across width below circle and text panel
        bar_start = (center_x, center_y + circle_diameter + 60)
        bar_end = (rect_x + gradient_width, bar_start[1])
        draw.line([bar_start, bar_end], fill=(255,255,255, 180), width=8)

        # Draw circle as playhead on progress bar (left start)
        playhead_center = (center_x + 20, bar_start[1])
        playhead_radius = 18
        draw.ellipse([playhead_center[0] - playhead_radius, playhead_center[1] - playhead_radius,
                      playhead_center[0] + playhead_radius, playhead_center[1] + playhead_radius], fill=(255,255,255))

        # Draw "0:00" at bottom-left below circle progress bar
        draw.text((center_x - 20, bar_start[1] - 40), "0:00", font=font_small, fill=(255,255,255))

        # Draw bot name at top-right corner
        draw.text((bg_width - 260, 20), unidecode(app.name), font=font_info, fill=(255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0))

        # Draw a modern play icon overlay near circle center-left
        play_icon_pos = (center_x + circle_radius - 90, center_y + circle_radius - 90)
        play_icon_radius = 70
        play_icon_color = (255, 100, 100, 180)
        draw.ellipse([play_icon_pos[0], play_icon_pos[1], play_icon_pos[0] + play_icon_radius*2, play_icon_pos[1] + play_icon_radius*2], fill=play_icon_color)

        # Draw triangle play shape inside circle
        triangle = [
            (play_icon_pos[0]+play_icon_radius*0.8, play_icon_pos[1]+play_icon_radius*0.5),
            (play_icon_pos[0]+play_icon_radius*1.8, play_icon_pos[1]+play_icon_radius),
            (play_icon_pos[0]+play_icon_radius*0.8, play_icon_pos[1]+play_icon_radius*1.5)
        ]
        draw.polygon(triangle, fill=(255,255,255))

        # Save final image and cleanup temp
        dark_background.save(cache_path)

        try:
            os.remove(f"cache/thumb_{videoid}.png")
        except Exception:
            pass

        return cache_path

    except Exception as e:
        print(f"Exception in get_thumb: {e}")
        return YOUTUBE_IMG_URL


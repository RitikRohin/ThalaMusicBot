import asyncio
import base64
import mimetypes
import os
from pyrogram import filters, types as t
from lexica import AsyncClient
from EsproMusic import app
from lexica.constants import languageModels
from typing import Union, Tuple

# In-memory user model storage
user_model_memory = {}

# --- Chat Completion function ---
async def ChatCompletion(prompt, model) -> Union[Tuple[str, list], str]:
    try:
        modelInfo = getattr(languageModels, model)
        client = AsyncClient()
        output = await client.ChatCompletion(prompt, modelInfo)
        if model == "bard":
            return output['content'], output['images']
        return output['content']
    except Exception as E:
        raise Exception(f"API error: {E}")

# --- Vision for Gemini with images ---
async def geminiVision(prompt, model, images) -> Union[Tuple[str, list], str]:
    imageInfo = []
    for image in images:
        with open(image, "rb") as imageFile:
            data = base64.b64encode(imageFile.read()).decode("utf-8")
            mime_type, _ = mimetypes.guess_type(image)
            imageInfo.append({
                "data": data,
                "mime_type": mime_type
            })
        os.remove(image)
    payload = {"images": imageInfo}
    modelInfo = getattr(languageModels, model)
    client = AsyncClient()
    output = await client.ChatCompletion(prompt, modelInfo, json=payload)
    return output['content']['parts'][0]['text']

# --- Extract media (image/doc) ---
def getMedia(message):
    media = message.media if message.media else message.reply_to_message.media if message.reply_to_message else None
    if message.media:
        if message.photo:
            media = message.photo
        elif message.document and message.document.mime_type in ['image/png', 'image/jpg', 'image/jpeg'] and message.document.file_size < 5242880:
            media = message.document
        else:
            media = None
    elif message.reply_to_message and message.reply_to_message.media:
        if message.reply_to_message.photo:
            media = message.reply_to_message.photo
        elif message.reply_to_message.document and message.reply_to_message.document.mime_type in ['image/png', 'image/jpg', 'image/jpeg'] and message.reply_to_message.document.file_size < 5242880:
            media = message.reply_to_message.document
        else:
            media = None
    return media

# --- Extract command text ---
def getText(message):
    text_to_return = message.text
    if message.text is None:
        return None
    if " " in text_to_return:
        try:
            return message.text.split(None, 1)[1]
        except IndexError:
            return None
    else:
        return None

# --- Command handler: /gpt /bard /gemini etc. ---
@app.on_message(filters.command(["gpt", "bard", "llama", "mistral", "palm", "gemini"]))
async def chatbots(_, m: t.Message):
    prompt = getText(m)
    media = getMedia(m)

    # Save user model for future messages
    model = m.command[0].lower()
    user_model_memory[m.from_user.id] = model

    if media is not None:
        return await askAboutImage(_, m, [media], prompt)

    if prompt is None:
        return await m.reply_text(f"✅ Model set to `{model}`. Ab bina command ke message bhejo.")

    output = await ChatCompletion(prompt, model)

    if model == "bard":
        output, images = output
        if not images:
            return await m.reply_text(output)
        media = [t.InputMediaPhoto(i) for i in images]
        media[0] = t.InputMediaPhoto(images[0], caption=output)
        return await _.send_media_group(m.chat.id, media, reply_to_message_id=m.id)

    await m.reply_text(output['parts'][0]['text'] if model == "gemini" else output)

# --- Auto-reply handler (no command) ---
@app.on_message(filters.private & filters.text & ~filters.command(["gpt", "bard", "llama", "mistral", "palm", "gemini"]))
async def smart_chat(_, m: t.Message):
    prompt = m.text
    if not prompt:
        return

    # Get user model or default to 'gpt'
    model = user_model_memory.get(m.from_user.id, "gpt")

    try:
        output = await ChatCompletion(prompt, model)
        await m.reply_text(output['parts'][0]['text'] if model == "gemini" else output)
    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")

# --- Handle image + prompt for Gemini ---
async def askAboutImage(_, m: t.Message, mediaFiles: list, prompt: str):
    images = []
    for media in mediaFiles:
        image = await _.download_media(media.file_id, file_name=f'./downloads/{m.from_user.id}_ask.jpg')
        images.append(image)
    output = await geminiVision(prompt if prompt else "What's this?", "geminiVision", images)
    await m.reply_text(output)

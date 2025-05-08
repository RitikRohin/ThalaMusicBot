# group_vc_playback.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType

from EsproMusic import app  # Make sure your Pyrogram Client is named app or update accordingly

# Temporary in-memory mapping (replace with persistent DB logic)
vc_group_map = {}

async def set_vc_group(from_id: int, to_id: int):
    vc_group_map[from_id] = to_id

async def get_vc_group(from_id: int):
    return vc_group_map.get(from_id)

# Command to set VC target group
@app.on_message(filters.command("setvcgroup") & filters.group)
async def set_vc(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setvcgroup <target_group_id>")

    try:
        target_id = int(message.command[1])
        chat = await app.get_chat(target_id)
        if chat.type != ChatType.SUPERGROUP:
            return await message.reply("Please provide a valid supergroup ID.")

        await set_vc_group(message.chat.id, target_id)
        return await message.reply(f"VC group set successfully! Now music from this group will play in {chat.title}.")
    except Exception as e:
        return await message.reply(f"Error: {e}")

# GPlay command to trigger music in linked VC group
@app.on_message(filters.command("gplay") & filters.group)
async def gplay_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /gplay <song name or link>")

    query = message.text.split(None, 1)[1]
    from_group_id = message.chat.id
    to_group_id = await get_vc_group(from_group_id) or from_group_id  # Default to current group if not mapped

    # Your existing playback code goes here
    # Example: await play_music(to_group_id, query)
    await message.reply(f"Simulated: Playing '{query}' in group ID {to_group_id}...")

    # Send VC join link
    try:
        link = await app.create_chat_invite_link(to_group_id)
        await message.reply(
            f"Join the voice chat where music is playing:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join VC", url=link.invite_link)]
            ])
        )
    except Exception as e:
        await message.reply(f"Playback started, but couldn't create invite link: {e}")

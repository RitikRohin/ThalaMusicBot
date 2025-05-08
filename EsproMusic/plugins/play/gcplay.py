from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatType

from EsproMusic import app
from EsproMusic.utils.database import set_gmode
from EsproMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS

@app.on_message(filters.command(["groupplay"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def groupmode_(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text("Please provide a group username or 'disable'/'linked'.")

    query = message.text.split(None, 2)[1].lower().strip()

    if query == "disable":
        await set_gmode(message.chat.id, None)
        return await message.reply_text("GroupPlay mode disabled. Songs will now play here.")

    elif query == "linked":
        chat = await app.get_chat(message.chat.id)
        if chat.linked_chat and chat.linked_chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            group_id = chat.linked_chat.id
            await set_gmode(message.chat.id, group_id)
            return await message.reply_text(f"Connected with linked group: {chat.linked_chat.title}")
        else:
            return await message.reply_text("No linked group found or invalid type.")

    else:
        try:
            chat = await app.get_chat(query)
        except:
            return await message.reply_text("Could not find that group.")

        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return await message.reply_text("Provided username is not a valid group.")

        try:
            members = await app.get_chat_members(chat.id)
        except:
            return await message.reply_text("Unable to fetch group members.")

        # Optional: ownership check (can be skipped)
        await set_gmode(message.chat.id, chat.id)
        return await message.reply_text(f"Successfully connected to: {chat.title}")

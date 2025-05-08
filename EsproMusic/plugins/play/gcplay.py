from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatType

from EsproMusic import app
from EsproMusic.utils.database import set_cmode
from EsproMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS


@app.on_message(filters.command(["gplay"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def playmode_(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["cplay_1"].format(message.chat.title))
    
    query = message.text.split(None, 2)[1].lower().strip()
    
    if query == "disable":
        await set_cmode(message.chat.id, None)
        return await message.reply_text(_["cplay_7"])
    
    elif query == "linked":
        chat = await app.get_chat(message.chat.id)
        if chat.linked_chat:
            chat_id = chat.linked_chat.id
            if chat.linked_chat.type != ChatType.SUPERGROUP:
                return await message.reply_text("Linked chat must be a group, not a channel.")
            await set_cmode(message.chat.id, chat_id)
            return await message.reply_text(
                _["cplay_3"].format(chat.linked_chat.title, chat.linked_chat.id)
            )
        else:
            return await message.reply_text(_["cplay_2"])
    
    else:
        return await message.reply_text("Only 'linked' groups are supported, not channels.")

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatType
from pyrogram.types import Message

from EsproMusic import app
from EsproMusic.utils.database import set_cmode
from EsproMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS


@app.on_message(filters.command(["groupplay"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def playmode_(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["gplay_1"].format(message.chat.title))

    query = message.text.split(None, 2)[1].lower().strip()

    if query == "disable":
        await set_cmode(message.chat.id, None)
        return await message.reply_text(_["gplay_7"])

    elif query == "linked":
        chat = await app.get_chat(message.chat.id)
        if chat.linked_chat:
            chat_id = chat.linked_chat.id
            await set_cmode(message.chat.id, chat_id)
            return await message.reply_text(
                _["gplay_3"].format(chat.linked_chat.title, chat.linked_chat.id)
            )
        else:
            return await message.reply_text(_["gplay_2"])

    else:
        try:
            chat = await app.get_chat(query)
        except:
            return await message.reply_text(_["gplay_4"])

        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return await message.reply_text(_["gplay_5"])

        if chat.id == message.chat.id:
            return await message.reply_text("You cannot link the same group to itself.")

        # Check if the command sender is an admin in the target group
        is_admin = False
        try:
            async for member in app.get_chat_members(chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
                if member.user.id == message.from_user.id:
                    is_admin = True
                    break
        except:
            return await message.reply_text(_["gplay_4"])

        if not is_admin:
            return await message.reply_text(_["gplay_6"].format(chat.title, chat.id))

        await set_cmode(message.chat.id, chat.id)
        return await message.reply_text(_["gplay_3"].format(chat.title, chat.id))

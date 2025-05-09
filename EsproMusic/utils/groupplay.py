from EsproMusic import app
from EsproMusic.utils.database import get_cmode
from pyrogram.enums import ChatType


async def get_grouplayCB(_, command, CallbackQuery):
    if command == "g":
        chat_id = await get_cmode(CallbackQuery.message.chat.id)
        if chat_id is None:
            try:
                return await CallbackQuery.answer(_["setting_7"], show_alert=True)
            except:
                return None, None
        try:
            chat = await app.get_chat(chat_id)
            if chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL]:
                return await CallbackQuery.answer(_["gplay_5"], show_alert=True)
            title = chat.title
        except:
            try:
                return await CallbackQuery.answer(_["gplay_4"], show_alert=True)
            except:
                return None, None
    else:
        chat_id = CallbackQuery.message.chat.id
        title = None

    return chat_id, title

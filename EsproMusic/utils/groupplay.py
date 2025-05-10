from EsproMusic import app
from EsproMusic.utils.database import get_cmode
from pyrogram.enums import ChatType


async def get_groupplayCB(_, command, CallbackQuery):
    if command == "g":
        linked_chat_id = await get_cmode(CallbackQuery.message.chat.id)
        if not linked_chat_id:
            return await CallbackQuery.answer(_["setting_13"], show_alert=True)

        try:
            chat = await app.get_chat(linked_chat_id)
        except:
            return await CallbackQuery.answer(_["gplay_4"], show_alert=True)

        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return await CallbackQuery.answer("Only groups are supported, not channels.", show_alert=True)

        return linked_chat_id, chat.title

    return CallbackQuery.message.chat.id, None

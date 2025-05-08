from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from EsproMusic import app
from EsproMusic.utils.database import set_cmode
from EsproMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS

@app.on_message(filters.command(["groupplay", "gplaymode"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def groupplay_(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/groupplay [disable | group_id | @username]`")

    query = message.command[1].strip().lower()

    if query == "disable":
        await set_cmode(message.chat.id, None)
        return await message.reply_text("✅ Group play mode disabled. Now playing in this group only.")

    try:
        target_chat = await app.get_chat(query)
    except Exception as e:
        return await message.reply_text("❌ Failed to find the group. Please check the username or ID.")

    if target_chat.type != ChatType.GROUP and target_chat.type != ChatType.SUPERGROUP:
        return await message.reply_text("❌ Only groups can be linked using this command.")

    # Check if user is admin in both groups (source and target)
    try:
        member = await app.get_chat_member(target_chat.id, message.from_user.id)
        if not member.status in ["administrator", "creator"]:
            return await message.reply_text("❌ You must be an **admin** in the target group.")
    except:
        return await message.reply_text("❌ Couldn't verify your admin rights in the target group.")

    # Optional: You can also check if bot is admin in the target group here.

    await set_cmode(message.chat.id, target_chat.id)
    return await message.reply_text(f"✅ Successfully linked group **{target_chat.title}** (`{target_chat.id}`) for playback.")

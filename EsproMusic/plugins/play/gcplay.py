from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from EsproMusic import app
from EsproMusic.utils.database import set_cmode
from EsproMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS


@app.on_message(filters.command(["groupplay", "gplaymode", "gpm"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def groupplay_(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/groupplay [disable | group_id | @username | invite_link]`")

    query = message.command[1].strip()

    if query.lower() == "disable":
        await set_cmode(message.chat.id, None)
        return await message.reply_text("✅ Group play mode disabled. Now playing in this group only.")

    try:
        # Accept invite link if user provides it
        if "t.me/joinchat/" in query or "t.me/+" in query:
            invited = await app.join_chat(query)
            target_chat = await app.get_chat(invited.id)
        else:
            target_chat = await app.get_chat(query)
    except Exception as e:
        print(f"[groupplay ERROR] Failed to get chat for query '{query}': {e}")
        return await message.reply_text("❌ Failed to find or join the group. Please check the username, ID, or invite link.")

    if target_chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return await message.reply_text("❌ Only groups can be linked using this command.")

    if target_chat.id == message.chat.id:
        return await message.reply_text("❌ This is already the current group.")

    # Check if user is admin in the target group
    try:
        member = await app.get_chat_member(target_chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.reply_text("❌ You must be an **admin** in the target group.")
    except Exception as e:
        print(f"[groupplay ERROR] User admin check failed: {e}")
        return await message.reply_text("❌ Couldn't verify your admin rights in the target group.")

    # Check if bot is admin in the target group
    try:
        bot_member = await app.get_chat_member(target_chat.id, client.me.id)
        if bot_member.status != "administrator":
            return await message.reply_text("❌ I'm not an **admin** in the target group. Please promote me first.")
    except Exception as e:
        print(f"[groupplay ERROR] Bot admin check failed: {e}")
        return await message.reply_text("❌ Couldn't verify my admin rights in the target group.")

    # Set the group play mode
    await set_cmode(message.chat.id, target_chat.id)
    return await message.reply_text(
        f"✅ Successfully linked group **{target_chat.title}** (`{target_chat.id}`) for playback."
    )

from pyrogram import filters
from pyrogram.types import Message
from EsproMusic import app
from EsproMusic.utils.database.group_mapping import set_play_group

@app.on_message(filters.command("setvc") & filters.group)
async def set_vc_group(_, message: Message):
    if not message.from_user or not message.from_user.id:
        return

    if len(message.command) != 2:
        return await message.reply("Usage: `/setvc <group_b_id>`", quote=True)

    try:
        target_group_id = int(message.command[1])
        await set_play_group(message.chat.id, target_group_id)
        await message.reply(f"✅ All songs from this group will now play in Group ID `{target_group_id}` VC.", quote=True)
    except ValueError:
        await message.reply("Invalid Group ID.")

from pyrogram import filters
from pyrogram.types import Message
from EsproMusic import app
from EsproMusic.utils.database import get_play_group

# Replace this with your actual play logic
from EsproMusic.core.player import stream_song

@app.on_message(filters.command("gplay") & filters.group)
async def gplay_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/gplay <song name>`", quote=True)

    query = " ".join(message.command[1:])
    source_group_id = message.chat.id
    target_group_id = await get_play_group(source_group_id)

    if not target_group_id:
        return await message.reply("❌ No VC group set. Use `/setvc <group_b_id>` first.", quote=True)

    try:
        await stream_song(chat_id=target_group_id, query=query, requester=message.from_user.mention)
        await message.reply(f"▶️ Playing **{query}** in Group `{target_group_id}` VC.", quote=True)
    except Exception as e:
        await message.reply(f"Error: {e}")

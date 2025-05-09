

from EsproMusic import app
from config import DURATION_LIMIT
from EsproMusic.platforms.Youtube import yt_stream

async def stream_song(chat_id: int, query: str, requester: str):
    # 1. Download song via yt-dlp or search it
    title, path = await yt_stream(query)

    # 2. Join VC and play (use your existing VC join/play logic here)
    await pytgcalls.join_group_call(
        chat_id,
        path,
        stream_type="local",  # or input-stream depending on your player
    )
    # Optional: store song info, logs, etc.



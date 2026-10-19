import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
STORAGE_CHAT = os.getenv("STORAGE_CHAT", "me")

SESSION_DIR = Path("/app/session")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

client = TelegramClient(
    str(SESSION_DIR / "infistore"),
    API_ID,
    API_HASH,
)


async def connect():
    await client.start()
    print("Telegram storage connected.")


async def upload_file(path: str, caption: str):
    return await client.send_file(
        STORAGE_CHAT,
        path,
        caption=caption,
        force_document=True,
    )


async def download_file(message_id: int, destination: str):
    message = await client.get_messages(STORAGE_CHAT, ids=message_id)
    if not message:
        raise FileNotFoundError("Telegram message not found.")
    return await message.download_media(file=destination)


async def delete_message(message_id: int):
    await client.delete_messages(STORAGE_CHAT, message_id)


async def get_message(message_id: int):
    return await client.get_messages(STORAGE_CHAT, ids=message_id)


async def iter_storage_messages(limit=None):
    async for message in client.iter_messages(
        STORAGE_CHAT,
        limit=limit,
        reverse=True,
    ):
        yield message

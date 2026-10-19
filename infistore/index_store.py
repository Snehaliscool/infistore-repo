import json
import hashlib
from datetime import datetime, timezone

from storage import upload_file, download_file, delete_message, get_message

INDEX_MARKER = "infistore_INDEX_V2"
INDEX_FILENAME = ".infistore-index.json"


def empty_index():
    return {
        "version": 2,
        "updated_at": None,
        "files": [],
    }


def encode_index(index):
    return json.dumps(
        index,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def checksum(data: bytes):
    return hashlib.sha256(data).hexdigest()


async def find_index_message():
    # The current index message ID is discovered from Telegram itself.
    # We use the newest matching marker.
    from storage import iter_storage_messages

    found = None
    async for message in iter_storage_messages():
        if (
            message
            and message.file
            and message.message
            and message.message.startswith(INDEX_MARKER)
        ):
            found = message
    return found


async def load_index():
    message = await find_index_message()

    if not message:
        return empty_index(), None

    path = f"/tmp/infistore/{INDEX_FILENAME}"
    await download_file(message.id, path)

    try:
        with open(path, "rb") as f:
            data = f.read()

        index = json.loads(data.decode("utf-8"))

        if index.get("version") != 2:
            raise ValueError("Unsupported index version")

        return index, message.id
    finally:
        import os
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


async def save_index(index, old_message_id=None):
    index["updated_at"] = datetime.now(timezone.utc).isoformat()

    data = encode_index(index)

    path = f"/tmp/infistore/{INDEX_FILENAME}"

    with open(path, "wb") as f:
        f.write(data)

    caption = (
        f"{INDEX_MARKER}\n"
        f"sha256:{checksum(data)}"
    )

    message = await upload_file(path, caption)

    if old_message_id:
        try:
            await delete_message(old_message_id)
        except Exception:
            pass

    import os
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    return message.id


async def add_record(record):
    index, old_id = await load_index()

    # Avoid duplicate Telegram message IDs.
    index["files"] = [
        x for x in index["files"]
        if x.get("telegram_message_id") != record["telegram_message_id"]
    ]

    index["files"].append(record)

    await save_index(index, old_id)


async def remove_record(file_id):
    index, old_id = await load_index()

    index["files"] = [
        x for x in index["files"]
        if x["id"] != file_id
    ]

    await save_index(index, old_id)


async def get_index():
    index, _ = await load_index()
    return index

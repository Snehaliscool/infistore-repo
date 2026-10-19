import hashlib
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from storage import (
    connect,
    upload_file,
    download_file,
    delete_message,
    client,
)
from index_store import (
    get_index,
    add_record,
    remove_record,
)

app = FastAPI(title="infistore")

TEMP_DIR = Path("/tmp/infistore")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup():
    await connect()


@app.on_event("shutdown")
async def shutdown():
    await client.disconnect()


@app.get("/api/files")
async def list_files():
    index = await get_index()
    return index["files"]


@app.get("/api/status")
async def status():
    index = await get_index()
    return {
        "version": index["version"],
        "file_count": len(index["files"]),
        "index_updated_at": index["updated_at"],
        "storage": "telegram",
    }


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    safe_name = Path(file.filename or "unnamed").name
    suffix = Path(safe_name).suffix

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=TEMP_DIR,
    )
    temp_path = Path(temp_file.name)

    try:
        sha256 = hashlib.sha256()
        size = 0

        with temp_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)
                sha256.update(chunk)
                size += len(chunk)

        file_id = uuid.uuid4().hex

        caption = (
            f"infistore_FILE_V2\n"
            f"id:{file_id}\n"
            f"name:{safe_name}"
        )

        message = await upload_file(
            str(temp_path),
            caption,
        )

        record = {
            "id": file_id,
            "name": safe_name,
            "size": size,
            "sha256": sha256.hexdigest(),
            "mime_type": file.content_type,
            "telegram_message_id": message.id,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

        await add_record(record)

        return {
            "success": True,
            "file": record,
        }

    finally:
        temp_path.unlink(missing_ok=True)


@app.get("/api/download/{file_id}")
async def download(file_id: str):
    index = await get_index()

    record = next(
        (x for x in index["files"] if x["id"] == file_id),
        None,
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    safe_name = Path(record["name"]).name
    output = TEMP_DIR / f"{file_id}_{safe_name}"

    await download_file(
        record["telegram_message_id"],
        str(output),
    )

    return FileResponse(
        path=output,
        filename=safe_name,
        media_type=record["mime_type"] or "application/octet-stream",
        background=None,
    )


@app.delete("/api/files/{file_id}")
async def delete(file_id: str):
    index = await get_index()

    record = next(
        (x for x in index["files"] if x["id"] == file_id),
        None,
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    await delete_message(
        record["telegram_message_id"]
    )

    await remove_record(file_id)

    return {"success": True}


app.mount(
    "/",
    StaticFiles(directory="static", html=True),
    name="static",
)

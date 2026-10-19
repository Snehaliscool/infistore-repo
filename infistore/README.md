# TeleStore V2

Telegram is used as the cloud backend for both:

1. Actual files
2. The file index/manifest

There is deliberately **no SQLite database**.

## Architecture

```text
Browser
   |
   v
FastAPI
   |
   +---- temporary upload/download data
   |
   v
Telegram
   |
   +---- files
   |
   +---- encrypted-ready manifest location
```

The canonical file catalogue is a `.json` document stored as a special Telegram document message.

When the application starts on a new machine, it reads the index from Telegram.

## Setup

### 1. Get Telegram API credentials

Open:

https://my.telegram.org

Go to API development tools and create an application.

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_hash
STORAGE_CHAT=me
```

`STORAGE_CHAT=me` means the dedicated Telegram storage account's Saved Messages.

### 3. Start

```bash
docker compose up -d --build
```

Then:

```bash
docker compose logs -f
```

On first startup Telethon asks for the phone number, Telegram login code, and 2FA password if enabled.

Open:

http://127.0.0.1:8000

## Moving to another computer

Install the project and log into the same Telegram storage account.

The index is in Telegram, so there is no local database to copy.

The Docker session volume is still local and contains your Telegram authentication session.

## What is stored locally?

Persistent:

- Telegram session
- Docker volume metadata

Not persistent:

- uploaded files
- downloaded files
- file index

Temporary upload/download data is written under `/tmp/telestore` and removed after use.

## Important limitation

This version uses the server as a temporary relay:

Browser -> FastAPI -> temporary file -> Telegram

and:

Telegram -> temporary file -> browser

A future streaming implementation can reduce local disk use further.

## Index safety

The index is rewritten as a new Telegram document whenever files are added or removed. The previous index is deleted only after the new index has been uploaded.

The index includes SHA-256 hashes for files.

## Security

Do not expose this application publicly without authentication and HTTPS.

Treat `.env` and the Telegram session volume as secrets.

The index is currently plain JSON in Telegram. Do not put sensitive metadata in it until client-side encryption is added.

## Recovery

If the Docker container is destroyed but the Telegram session remains unavailable, you can authenticate again with the same Telegram account and recover the index from Telegram.

If the index itself is deleted or corrupted, the next version can rebuild it automatically by scanning messages tagged `TELESTORE_FILE_V2`.

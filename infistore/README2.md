# Infistore

**Infistore** is a Telegram-backed personal cloud storage system.

Your files are stored in your Telegram account, while Infistore provides a simple web interface to upload, browse, download, and delete them.

---

## Architecture

```text
              ┌─────────────────┐
              │    Browser      │
              │  Infistore GUI  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │    FastAPI      │
              │     Server      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │    Telegram     │
              │                 │
              │  Actual Files   │
              │  File Index     │
              └─────────────────┘
```

Infistore does **not** use a traditional cloud storage provider for the actual files.

The files and the Infistore index are stored in Telegram.

Docker only provides the application environment, Telegram session storage, and temporary upload/download space.

---

# Requirements

You need:

* Docker
* Docker Compose
* A Telegram account
* Telegram API credentials

You do **not** need Python installed on your host machine because Python runs inside Docker.

---

# 1. Get Telegram API Credentials

Go to:

https://my.telegram.org

Log in with your Telegram account.

Open:

**API development tools**

Create an application and obtain:

```text
API ID
API Hash
```

You will need both.

---

# 2. Configure Infistore

Copy the example environment file:

```fish
cp .env.example .env
```

Open it:

```fish
nano .env
```

Put your credentials inside:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
STORAGE_CHAT=me
```

### `STORAGE_CHAT=me`

This means Infistore uses your Telegram **Saved Messages** as the storage location.

Your files will appear in your own Telegram Saved Messages.

---

# 3. Build Infistore

Build the Docker image:

```fish
docker compose build
```

This may take a little while the first time.

---

# 4. Authenticate Telegram

**Important:** Do not start Infistore with `docker compose up -d` before completing the first Telegram login.

Run:

```fish
docker compose run --rm -it infistore python auth.py
```

You should see:

```text
Please enter your phone (or bot token):
```

Enter your Telegram number using international format.

Example:

```text
+919441688808
```

Press Enter.

Telegram will send you a login code.

Enter the code when requested.

If you have Telegram Two-Step Verification enabled, enter your Telegram password when requested.

After successful authentication you should see:

```text
Infistore Telegram authentication successful.
Session saved. Now run: docker compose up -d
```

---

# 5. Start Infistore

Now start the web server:

```fish
docker compose up -d
```

Check the container:

```fish
docker compose ps
```

You should see something similar to:

```text
NAME        SERVICE      STATUS
infistore   infistore    Up
```

The port should be:

```text
0.0.0.0:8000->8000/tcp
```

---

# 6. Open Infistore

Open your browser:

```text
http://127.0.0.1:8000
```

or:

```text
http://localhost:8000
```

You should see the Infistore interface.

---

# 7. Test the Server

You can test the server from your terminal:

```fish
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "ok": true,
  "service": "infistore"
}
```

If you get this response, the server is running correctly.

---

# 8. Upload a File

From the Infistore web interface:

1. Click **Choose files**
2. Select a file
3. Wait for the upload
4. The file will appear in the file list

The actual file is uploaded to your Telegram Saved Messages.

---

# 9. Download a File

Click:

```text
Download
```

next to a file.

Infistore retrieves the file from Telegram and sends it to your browser.

---

# 10. Delete a File

Click:

```text
Delete
```

Infistore will:

1. Delete the file from Telegram
2. Update the Infistore index

---

# Docker Commands

### Start

```fish
docker compose up -d
```

### Stop

```fish
docker compose down
```

### Restart

```fish
docker compose restart
```

### Rebuild

Use this after changing the source code:

```fish
docker compose up -d --build
```

### View logs

```fish
docker compose logs -f
```

### Check container status

```fish
docker compose ps
```

### Check the health endpoint

```fish
curl http://127.0.0.1:8000/health
```

---

# Telegram Authentication

The Telegram session is stored in a Docker volume:

```text
infistore_session
```

After the first successful login, you normally do **not** need to authenticate again.

If you intentionally delete the Docker volumes:

```fish
docker compose down -v
```

the Telegram session will also be deleted.

You will then need to authenticate again:

```fish
docker compose run --rm -it infistore python auth.py
```

**Avoid `docker compose down -v` unless you know you want to remove the local session.**

Your actual files remain in Telegram.

---

# Storage Model

Infistore uses Telegram as the storage backend.

```text
Telegram
│
├── Your files
│
└── Infistore index
```

The index keeps information such as:

```text
File ID
Filename
File size
SHA-256
Telegram message ID
```

This allows Infistore to associate the web interface's file records with the corresponding Telegram files.

---

# Local Disk Usage

Infistore is designed so that the **persistent files are stored in Telegram**.

However, the current implementation temporarily uses Docker storage for:

* Upload processing
* Download processing
* Telegram session
* Index processing

Therefore, Infistore is **not completely zero-disk**.

The important distinction is:

```text
Persistent file storage
        ↓
     Telegram

Temporary processing
        ↓
     Docker
```

---

# Accessing Infistore From Another Device

If Infistore is running on your computer and you want to access it from another device on the same network, find your computer's LAN IP:

```fish
ip addr
```

For example, if your computer has:

```text
192.168.1.25
```

you can access:

```text
http://192.168.1.25:8000
```

from another device on the same network.

Make sure your firewall allows TCP port `8000`.

---

# Troubleshooting

## Container keeps restarting

Run:

```fish
docker compose logs --tail=100
```

If you see:

```text
EOFError: EOF when reading a line
```

Infistore is trying to authenticate Telegram from a non-interactive container.

Run:

```fish
docker compose run --rm -it infistore python auth.py
```

Complete the Telegram login, then:

```fish
docker compose up -d
```

---

## Browser says connection refused

Check:

```fish
docker compose ps
```

Then:

```fish
curl http://127.0.0.1:8000/health
```

If the curl request fails, check:

```fish
docker compose logs --tail=100
```

---

## Port 8000 is already in use

Check:

```fish
ss -ltnp | grep 8000
```

You can change the host port in `docker-compose.yml`.

For example:

```yaml
ports:
  - "8080:8000"
```

Then access:

```text
http://127.0.0.1:8080
```

---

# Project Structure

```text
infistore/
│
├── app.py
├── auth.py
├── storage.py
├── index_store.py
│
├── static/
│   └── index.html
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# Security Notes

Never commit your `.env` file.

Your `.env` contains your Telegram API credentials.

Make sure it remains ignored by Git:

```text
.env
```

Also, the Infistore web interface currently does not provide its own user authentication layer. It should therefore **not be exposed directly to the public internet without adding authentication and HTTPS**.

---

# Quick Start

Once `.env` is configured, the complete first-time setup is:

```fish
docker compose build

docker compose run --rm -it infistore python auth.py

docker compose up -d

docker compose ps

curl http://127.0.0.1:8000/health
```

Then open:

```text
http://127.0.0.1:8000
```

That's it.

---

## Infistore

**Your files. Your Telegram. Your storage interface.**

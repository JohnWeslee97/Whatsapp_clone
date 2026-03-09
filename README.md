A real-time chat application built with Django Channels and WebSockets, inspired by WhatsApp Web. Features instant messaging, online/offline status, read receipts, and a clean responsive UI.



✨ Features

🔐 User Authentication (Register / Login / Logout)

💬 Real-time messaging using WebSockets

✅ Read receipts

✓ — Message sent (receiver offline)

✓✓ — Message delivered (receiver online)

✓✓ 🔵 — Message read (receiver opened chat)


🟢 Online / Offline status with last seen

😊 Emoji picker

🔍 Search users

📱 Mobile responsive (WhatsApp Web style)

🔄 Auto reconnect on connection loss

🛡️ Custom error pages (404, 500, 403)

👨‍💼 Admin panel


🛠️ Tech Stack

TechnologyPurposeDjango 6.xBackend frameworkDjango ChannelsWebSocket supportDaphneASGI serverSQLiteDatabaseWhitenoiseStatic files (production)HTML / CSS / JSFrontend


⚙️ Local Installation

Step 1 — Clone the repository

bashgit clone https://github.com/YOUR_USERNAME/whatsapp-clone.git

cd whatsapp-clone

Step 2 — Create virtual environment

bashpython -m venv .venv

Step 3 — Activate virtual environment

bash# Windows

.venv\Scripts\activate

Step 4 — Install all dependencies

bash : pip install -r requirements.txt

Step 5 — Run migrations

bash : python manage.py migrate

Step 6 — Create superuser (for admin panel)

bash : python manage.py createsuperuser

Step 7 — Run the server

bash : python -m daphne -p 8000 Whatsapp_clone.asgi:application

Step 8 — Open in browser

http://127.0.0.1:8000

🔑 Environment Variables

VariableDescriptionDefault (local)SECRET_KEYDjango secret keyinsecure fallback keyDEBUGDebug modeTrueALLOWED_HOSTSAllowed hosts*DB_PATHSQLite database pathdb.sqlite3 (project root)CSRF_TRUSTED_ORIGINSTrusted origins for CSRFyour Railway domain

🚀 Deploy on Railway

Step 1 — Push to GitHub

bashgit add .

git commit -m "initial commit"

git push

Step 2 — Create Railway project

Go to railway.app

Login with GitHub

Click New Project → Deploy from GitHub repo

Select your repository

Wait for build to complete

Step 3 — Add Volume (persistent SQLite storage)

In your project click + New → Volume

Set Mount Path: /data

Set Size: 1 GB

Click Create

Step 4 — Set Environment Variables

Go to your service → Variables tab and add:

SECRET_KEY            → generate with command below

DEBUG                 → False

ALLOWED_HOSTS         → your-app.up.railway.app

DB_PATH               → /data/db.sqlite3

CSRF_TRUSTED_ORIGINS  → https://your-app.up.railway.app

Generate a secret key:

bashpython -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

Step 5 — Set Replicas to 1

Settings tab → Replicas → set to 1

⚠️ Important: InMemoryChannelLayer only works with 1 instance

Step 6 — Generate Domain

Settings tab → Networking → Generate Domain

Copy your domain e.g. your-app.up.railway.

Update ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS with this domain

Step 7 — Create superuser on Railway

Go to Railway dashboard

Click your service → Shell tab
Run:

bashpython manage.py createsuperuser

Step 8 — Visit your app

https://your-app.up.railway.app/login/

👨‍💼 Admin Panel

Local:    http://127.0.0.1:8000/admin/

Railway:  https://your-app.up.railway.app/admin/

Login with your superuser credentials to manage:

👥 Users

💬 Messages

👤 Profiles


💬 How It Works

Real-time Messaging

User sends message
      ↓
Django Channels WebSocket (ChatConsumer)
      ↓
Message saved to SQLite
      ↓
Broadcast to chat room group
      ↓
Receiver gets message instantly

Online Status

User logs in / opens page
      ↓
OnlineConsumer WebSocket connects
      ↓
Profile.is_online = True
      ↓
Broadcast to all users in online_users group
      ↓
All contacts see 🟢 Online instantly
Read Receipts

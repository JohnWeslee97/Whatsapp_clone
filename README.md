# WhatsApp Clone

A real-time chat application built with Django Channels and WebSockets, inspired by WhatsApp Web. It supports instant messaging, online/offline status, read receipts, emoji picker, user search, and a fully responsive mobile layout.

---

## Features

This project includes user authentication with register, login, and logout. Messages are sent and received in real time using WebSockets without any page refresh. It shows read receipts — a single tick when the message is sent, a double tick when the receiver is online, and a double blue tick when the receiver reads the message. Users can see each other's online or offline status along with the last seen time. There is also an emoji picker, user search to start new chats, auto reconnect on connection loss, custom error pages for 404, 500, and 403, and an admin panel to manage users, messages, and profiles.

---

## Tech Stack

The backend is built with Django 6 and Django Channels for WebSocket support. Daphne is used as the ASGI server. SQLite is used as the database. Whitenoise serves static files in production. The frontend uses plain HTML, CSS, and JavaScript.

---

## Local Installation

First clone the repository and navigate into the project folder.

```bash
git clone https://github.com/JohnWeslee97/Whatsapp_clone.git
cd Whatsapp_clone
```

Create and activate a virtual environment.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

Install all dependencies from requirements.txt.

```bash
pip install -r requirements.txt
```

Run the database migrations.

```bash
python manage.py migrate
```

Create a superuser to access the admin panel.

```bash
python manage.py createsuperuser
```

Start the server using Daphne.

```bash
python -m daphne -p 8000 Whatsapp_clone.asgi:application
```

Open your browser and go to http://127.0.0.1:8000 to use the app.

---

## Deploying on Railway

Push your code to GitHub first. Then go to railway.app and login with your GitHub account. Create a new project and select deploy from GitHub repo. Choose your repository and wait for the build to complete.

Add a Volume to store the SQLite database. Set the mount path to /data and size to 1 GB. Then go to the Variables tab and add the following environment variables.

```
SECRET_KEY            → your generated secret key
DEBUG                 → False
ALLOWED_HOSTS         → your-app.up.railway.app
DB_PATH               → /data/db.sqlite3
CSRF_TRUSTED_ORIGINS  → https://your-app.up.railway.app
```

To generate a secure secret key run this command and copy the output.

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Go to the Settings tab and set Replicas to 1. This is important because InMemoryChannelLayer only works with exactly one server instance. Then go to Networking and click Generate Domain to get your app URL. Update ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS with your domain.

To create a superuser on Railway, open the Shell tab in your service and run python manage.py createsuperuser. Once done, visit your app at https://your-app.up.railway.app/login/.

---

## Admin Panel

The admin panel is available at /admin/ on both local and production. Login with your superuser credentials to manage users, messages, and profiles.

---

## Common Issues

If CSS is not loading locally, make sure DEBUG is set to True in settings.py. Django only serves static files automatically in debug mode.

If WebSocket connection fails on Railway, make sure Replicas is set to 1, ALLOWED_HOSTS includes your Railway domain, and CSRF_TRUSTED_ORIGINS includes your full https domain.

If you see a 403 CSRF error, add your Railway domain to CSRF_TRUSTED_ORIGINS in settings.py.

If the database is not working on Railway, make sure the Volume is attached with mount path /data and DB_PATH is set to /data/db.sqlite3 in the Variables tab.

---

## Known Limitations

This project uses InMemoryChannelLayer which only works with one server instance. SQLite is not recommended for high traffic applications. For a production-ready setup with multiple users, switching to PostgreSQL and Redis is recommended.

---

## Future Improvements

Typing indicator, profile pictures, message delete and edit, group chat, push notifications, and PostgreSQL with Redis support are planned for future versions.

---

## License

MIT License — free to use and modify.
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

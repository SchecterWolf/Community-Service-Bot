# 🚓 Community Service Bot

Discord bot that sends naughty users to community service.

---

## 📚 Table of Contents
- [About the Bot](#about-the-bot)
- [How to Install](#how-to-install)
- [Configuration Options](#configuration-options)
- [How to Run](#how-to-run)

---

## 📖 About the Bot

**Community Service Bot** is a Discord moderation and fun utility bot designed to send users to *community service*.

When a user is placed into community service:
- They lose access to the rest of the Discord server
- They are restricted to a designated channel
- They must complete a **community service game** to be released

This makes it:
- ✅ Useful for handling legitimately problematic users  
- 🎭 Perfect for lighthearted trolling and engagement  

---

## ⚙️ How to Install

### Requirements
- Linux
- Python 3
- SQLite3
- pip
- bash
- git

---

### Installation Steps

#### 1. Clone the Repository
```bash
git clone git@github.com:SchecterWolf/Community-Service-Bot.git
cd Community-Service-Bot
```

#### 2. Create and Configure a Discord Bot
- Follow the official Discord guide to register a bot and obtain a bot token
- Place your bot token in:
```
config/token.txt
```

#### 3. Configure the Bot
- Edit:
```
config/config.json
```
(See [Configuration Options](#configuration-options))

---

### Discord Server Setup

Configure your server as follows:

#### Roles
- Ensure the bot role is **above all roles it will manage**
- Create:
  - `Community Service`
  - `JailMod`

#### Channels
- Create a channel:
  - `Community Service`

#### Permissions

- For **all channels**:
  - Add `Community Service` role
  - ❌ Remove `View Channel`

- For **Community Service channel**:
  - ❌ Remove `View Channel` for everyone
  - ✅ Allow `View Channel` for:
    - `Community Service`
    - `JailMod`

---

## 🔧 Configuration Options

Each server is configured using its **server ID** as the top-level key.

### Example `config.json`

```json
{
  "123456789012345678": {
    "AllowEmptyRoles": false,
    "CommunityServiceChannel": 111111111111111111,
    "CommunityServiceRole": 222222222222222222,
    "JailMod": 333333333333333333,
    "LogLevel": "debug"
  }
}
```

### Field Descriptions

| Field | Description |
|------|-------------|
| **Server ID** | The outermost key. Your Discord server ID |
| **AllowEmptyRoles** | `true` allows jailing users with no roles, `false` prevents it |
| **CommunityServiceChannel** | Channel ID for the *Community Service* channel |
| **CommunityServiceRole** | Role ID for the *Community Service* role |
| **JailMod** | Role ID for moderators who can manage jail actions |
| **LogLevel** | Logging level: `critical`, `error`, `warn`, `info`, `debug`, `none` |

---

## ▶️ How to Run

### Start the Bot

```bash
cd Community-Service-Bot
source ./venv.sh
./CommsBot.py
```

> 💡 On first run, the virtual environment will be created and dependencies installed automatically.

---

### 🔁 Run Automatically on Startup (Debian)

#### 1. Create a systemd Service File

```bash
sudo nano /etc/systemd/system/community-service-bot.service
```

#### 2. Add the Following

```ini
[Unit]
Description=Community Service Discord Bot
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/path/to/Community-Service-Bot
ExecStart=/bin/bash -c "source ./venv.sh && ./CommsBot.py"
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 3. Enable and Start the Service

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable community-service-bot
sudo systemctl start community-service-bot
```

#### 4. Check Status

```bash
sudo systemctl status community-service-bot
```

---

## 🧠 Notes

- Ensure your bot has permission to:
  - Manage roles
  - Send messages
  - Read message history
- The bot role **must be above** roles it modifies, or it will fail silently

---

## 🎯 Enjoy!

Turn punishment into participation — or just have some fun 😈


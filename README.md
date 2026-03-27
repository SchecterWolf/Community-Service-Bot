# 🚓 Community Service Bot

Discord bot that sends naughty users to community service.

---

## 📚 Table of Contents
- [About the Bot](#about-the-bot)
- [Community Service Games](#community-service-games)
- [How to Use the Bot](#how-to-use-the-bot)
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

## 🎮 Community Service Games

When a moderator assigns community service, they specify a number of **rounds**. Each game uses this value differently as described below.

### Supported Games

- **Counting**  
  The user must count from **0 up to the specified number of rounds**, sending one number per message.

- **Captcha**  
  The user must correctly solve **a number of captcha images equal to the rounds value**.

- **Math**  
  The user must solve **a number of simple math problems equal to the rounds value**.

- **Simon Says**  
  The user must click the correct button color matching what Simon says, for **the specified number of rounds**.

---

## 🤖 How to Use the Bot

Once the bot is installed and configured, all interactions are performed using **Discord slash commands** and context actions.

### Slash Commands

- **/give_comms**  
  Assigns community service to a user.  
  - Accepts a server member as input  
  - Opens a modal where the moderator selects:
    - Game type  
    - Number of rounds  
    - Reason for community service  

- **/echo**  
  The bot repeats any provided message.  
  Useful for moderators who want to **warn users anonymously**.

- **/help**  
  Available to users currently serving community service.  
  Provides assistance related to their current game/task.

---

### Context Menu Action

- **Move Message**  
  - Right-click a message in Discord  
  - Select **"Move Message"**  
  - Choose a destination channel  

This allows moderators to quickly relocate messages without copying or re-sending them manually.

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

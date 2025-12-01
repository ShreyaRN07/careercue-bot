-- Title:
CareerCue Bot – Intelligent Job Recommendation Telegram Bot

-- Content:

CareerCue Bot is an intelligent job‑recommendation system that helps users discover relevant opportunities based on their skills and interests. It uses a Telegram bot interface so users can interact easily and receive job suggestions directly in chat.​

-- Features

Collects user skills, preferences, and experience through a conversational Telegram bot.

Uses fuzzy matching and rule-based logic to compare user profiles with stored job data.

Stores profiles and job information in a local SQLite database.

Sends personalized job recommendations and updates as messages to users.

-- Tech Stack

Python (main.py, db.py, utility modules)

SQLite (careercu.db) for data storage

Telegram Bot API

Config file (config.ini) for tokens and settings

-- How to Run

Install dependencies:  
python-telegram-bot
requests
python-dotenv          # if you use .env instead of config.ini
configparser
sqlite3-binary         # or just use stdlib sqlite3, no install needed
pytz                   # if you handle timezones

Configuration (API keys and tokens)
The bot reads secrets from config.ini. Create this file in the project root (or edit the existing one) with the following sections:
[TELEGRAM]
bot_token = YOUR_TELEGRAM_BOT_TOKEN
[ADZUNA]
app_id = YOUR_ADZUNA_APP_ID
app_key = YOUR_ADZUNA_APP_KEY

How to get these values:

Telegram bot_token
Open Telegram and search for “BotFather”.
Use /newbot to create a bot, follow the prompts, and copy the HTTP API token given at the end.
Paste this token as bot_token in the [TELEGRAM] section.

Adzuna app_id and app_key
Go to the Adzuna Developer portal and create a free account.
Create a new application to get your app_id and app_key.
Paste them in the [ADZUNA] section of config.ini.
Create a Telegram bot via BotFather and paste the bot token into config.ini.

Run the bot
python main.py

Open Telegram, search for your bot, and start chatting to receive job recommendations.

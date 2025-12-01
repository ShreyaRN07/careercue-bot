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

Create a virtual environment and install dependencies:

pip install -r requirements.txt

Create a Telegram bot via BotFather and paste the bot token into config.ini.

Run the bot:

python main.py

Open Telegram, search for your bot, and start chatting to receive job recommendations.

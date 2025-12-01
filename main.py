import os
import configparser
from telegram.ext import CommandHandler
from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from utils.user_session import start_session, update_session, get_session, clear_session, mark_instructions_shown, has_shown_instructions
from utils.parse_profiles import extract_skills_from_profile
import requests
import smtplib
from email.mime.text import MIMEText
from db import init_db, save_user, save_jobs
import asyncio

# Load config from config.ini
config = configparser.ConfigParser()
config.read("config.ini")
BOT_TOKEN = config["TELEGRAM"]["bot_token"]

# Create data_profiles folder if it doesn't exist
os.makedirs("data_profiles", exist_ok=True)

# Define conversation states
ASK_JSON, ASK_LOCATION, ASK_SKILLS, ASK_CONFIRM, ASK_EMAIL = range(5)

# Example mapping: job title keywords -> required skills
JOB_ROLE_SKILLS = {
    "data scientist": {"Python", "Machine Learning", "SQL", "Statistics", "Pandas"},
    "web developer": {"HTML", "CSS", "JavaScript", "React", "Node.js"},
    "ui/ux designer": {"UI/UX", "Figma", "Adobe XD", "Wireframing", "Prototyping"},
    "software engineer": {"C++", "Java", "Python", "Algorithms", "Data Structures"},
    "cloud engineer": {"Cloud Computing", "AWS", "Azure", "Docker", "Kubernetes"},
}
# Example mapping: skill -> learning resource
SKILL_RESOURCES = {
    "Python": "https://www.coursera.org/specializations/python",
    "Machine Learning": "https://www.coursera.org/learn/machine-learning",
    "SQL": "https://www.codecademy.com/learn/learn-sql",
    "Statistics": "https://www.khanacademy.org/math/statistics-probability",
    "Pandas": "https://www.datacamp.com/courses/pandas-foundations",
    "HTML": "https://www.freecodecamp.org/learn/responsive-web-design/",
    "CSS": "https://www.freecodecamp.org/learn/responsive-web-design/",
    "JavaScript": "https://www.javascript.com/learn",
    "React": "https://react.dev/learn",
    "Node.js": "https://nodejs.dev/learn",
    "UI/UX": "https://www.coursera.org/specializations/ui-ux-design",
    "Figma": "https://www.coursera.org/learn/figma-ui-ux-design",
    "Adobe XD": "https://www.udemy.com/course/adobe-xd-ui-ux-design/",
    "Wireframing": "https://www.interaction-design.org/literature/topics/wireframing",
    "Prototyping": "https://www.interaction-design.org/literature/topics/prototyping",
    "C++": "https://www.learncpp.com/",
    "Java": "https://www.codecademy.com/learn/learn-java",
    "Algorithms": "https://www.coursera.org/specializations/algorithms",
    "Data Structures": "https://www.coursera.org/specializations/data-structures-algorithms",
    "Cloud Computing": "https://www.coursera.org/specializations/cloud-computing",
    "AWS": "https://www.aws.training/",
    "Azure": "https://learn.microsoft.com/en-us/training/azure/",
    "Docker": "https://www.docker.com/101-tutorial/",
    "Kubernetes": "https://www.coursera.org/learn/google-kubernetes-engine",
}

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    start_session(user_id)
    msg = await update.message.reply_text(
        "👋 Welcome to CareerCue Bot!\n\nPlease upload your LinkedIn `.json` profile file to continue."
    )
    session = get_session(user_id)
    if session is not None:
        session.setdefault("bot_message_ids", []).append(msg.message_id)

    return ASK_JSON

# File upload handler
async def receive_json(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    file_name = document.file_name
    file_path = os.path.join("data_profiles", file_name)

    file = await document.get_file()
    await file.download_to_drive(file_path)

    user_id = update.effective_user.id
    update_session(user_id, "json_file", file_path)  # Store file path in session

    session = get_session(user_id)
    await send_and_track_message(update, session, "📍 Now enter your preferred job location (e.g., Bangalore):")
    return ASK_LOCATION

# Location input handler
async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    location = update.message.text
    update_session(user_id, "location", location)

    session = get_session(user_id)
    await send_and_track_message(
        update, session,
        f"✅ All set! Here's what I received:\n\n"
        f"📄 File: {os.path.basename(session['json_file'])}\n"
        f"📍 Location: {session['location']}\n\n"
        f"Now extracting your skills..."
    )

    # Extract skills
    skills = extract_skills_from_profile(session['json_file'])
    session["skills"] = skills  # Store extracted skills in session

    await send_and_track_message(
        update, session,
        f"🧑‍💻 Skills extracted from your profile:\n"
        f"{', '.join(skills) if skills else 'No skills found.'}\n\n"
        "Would you like to add more skills? If yes, type them separated by commas. If not, type 'No'."
    )

    return ASK_SKILLS

# Skills confirmation handler
async def confirm_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_response = update.message.text.strip().lower()

    session = get_session(user_id)

    if user_response == "no":
        await update.message.reply_text("Got it! Proceeding to fetch job recommendations...")
    else:
        # Add more skills to the existing ones
        additional_skills = [skill.strip() for skill in user_response.split(",")]
        session["skills"].extend(additional_skills)
        await update.message.reply_text(
            f"✅ Skills updated! Here's the final list of your skills:\n"
            f"{', '.join(session['skills'])}\n\n"
            "Now fetching job recommendations..."
        )

    # Fetch jobs using the final skills list
    jobs = fetch_jobs(session["skills"], session["location"])

    # Save jobs to session
    session["jobs"] = jobs

    # Send jobs in Telegram
    for job in jobs:
        await send_and_track_message(
            update, session,
            f"💼 Job: {job['title']}\n"
            f"🏢 Company: {job['company']}\n"
            f"📍 Location: {job['location']}\n"
            f"🕒 Posted: {job.get('created', 'N/A')}\n"
            f"🔗 [Apply Here]({job['url']})\n"
            f"🎯 Match Score: {job['score']}%"
        )

    # Skill gap analysis for the first job
    if jobs and jobs[0]["title"] != "No jobs found":
        matched_role, missing_skills = skill_gap_analysis(session["skills"], jobs[0]["title"])
        if matched_role and missing_skills:
            resources = [
                f"[{skill}]({SKILL_RESOURCES.get(skill, 'https://www.google.com/search?q=' + skill + '+course')})"
                for skill in missing_skills
            ]
            await send_and_track_message(
                update, session,
                f"📈 *Skill Gap Analysis for '{matched_role.title()}'*\n"
                f"To improve your chances, consider learning: {', '.join(resources)}",
                parse_mode="Markdown"
            )
        else:
            await send_and_track_message(
                update, session,
                "🎉 You already have most of the key skills for this job role!"
            )

    await update.message.reply_text(
        "📧 Please enter your email address to receive these job recommendations:"
    )
    return ASK_EMAIL

async def receive_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    session = get_session(user_id)
    user_input = update.message.text.strip()

    extracted_skills = session.get("skills", [])
    added_skills = []
    if user_input.lower() != "no":
        added_skills = [s.strip() for s in user_input.split(",") if s.strip()]
        for skill in added_skills:
            if skill not in extracted_skills:
                extracted_skills.append(skill)
    session["skills"] = extracted_skills

    await send_and_track_message(
        update, session,
        f"🧑‍💻 Skills extracted from your profile: {', '.join(session.get('skills', [])) or 'No skills found.'}\n"
        f"➕ Skills you added: {', '.join(added_skills) if added_skills else 'None'}\n\n"
        f"👍 Final skill set: {', '.join(extracted_skills)}\n\n"
        "✅ Here is your information:\n"
        f"• File: {os.path.basename(session['json_file'])}\n"
        f"• Location: {session['location']}\n"
        f"• Skills: {', '.join(session['skills'])}\n\n"
        "Would you like to change anything?\n"
        "Type 'file' to re-upload your profile, 'location' to change location, 'skills' to update skills, or 'no' to continue."
    )

    return ASK_CONFIRM

# Confirm details handler
async def confirm_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_response = update.message.text.strip().lower()

    session = get_session(user_id)

    if user_response == "no":
        await update.message.reply_text("Got it! Proceeding to fetch job recommendations...")
    else:
        # User wants to update something
        if "file" in user_response:
            await update.message.reply_text("Please upload your updated LinkedIn `.json` profile file.")
            return ASK_JSON
        elif "location" in user_response:
            await update.message.reply_text("Please enter your preferred job location (e.g., Bangalore):")
            return ASK_LOCATION
        elif "skills" in user_response:
            await update.message.reply_text(
                "Please specify the additional skills you want to add, separated by commas.\n"
                "If you don't want to add any, type 'No'."
            )
            return ASK_SKILLS

    # Fetch jobs using the final skills list
    jobs = fetch_jobs(session["skills"], session["location"])

    # Save jobs to session
    session["jobs"] = jobs

    # Send jobs in Telegram
    for job in jobs:
        await send_and_track_message(
            update, session,
            f"💼 Job: {job['title']}\n"
            f"🏢 Company: {job['company']}\n"
            f"📍 Location: {job['location']}\n"
            f"🕒 Posted: {job.get('created', 'N/A')}\n"
            f"🔗 [Apply Here]({job['url']})\n"
            f"🎯 Match Score: {job['score']}%"
        )

    # Skill gap analysis for the first job
    if jobs and jobs[0]["title"] != "No jobs found":
        matched_role, missing_skills = skill_gap_analysis(session["skills"], jobs[0]["title"])
        if matched_role and missing_skills:
            resources = [
                f"[{skill}]({SKILL_RESOURCES.get(skill, 'https://www.google.com/search?q=' + skill + '+course')})"
                for skill in missing_skills
            ]
            await send_and_track_message(
                update, session,
                f"📈 *Skill Gap Analysis for '{matched_role.title()}'*\n"
                f"To improve your chances, consider learning: {', '.join(resources)}",
                parse_mode="Markdown"
            )
        else:
            await send_and_track_message(
                update, session,
                "🎉 You already have most of the key skills for this job role!"
            )

    await update.message.reply_text(
        "📧 Please enter your email address to receive these job recommendations:"
    )
    return ASK_EMAIL

def fetch_jobs(skills, location):
    config = configparser.ConfigParser()
    config.read("config.ini")
    app_id = config["ADZUNA"]["app_id"]
    app_key = config["ADZUNA"]["app_key"]

    jobs = []
    seen_urls = set()
    for skill in skills:
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 3,
            "what": skill,
            "where": location
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for result in data.get("results", []):
                job_url = result.get("redirect_url")
                if job_url not in seen_urls:
                    # Calculate match score
                    job_text = (result.get("title", "") + " " + result.get("description", "")).lower()
                    matched = sum(1 for s in skills if s.lower() in job_text)
                    score = int((matched / len(skills)) * 100) if skills else 0
                    jobs.append({
                        "title": result.get("title"),
                        "company": result.get("company", {}).get("display_name", ""),
                        "location": result.get("location", {}).get("display_name", location),
                        "url": job_url,
                        "score": score,
                        "created": result.get("created")  # Add posted timestamp
                    })
                    seen_urls.add(job_url)
        else:
            print("Adzuna API error:", response.status_code, response.text)
    if not jobs:
        jobs = [{
            "title": "No jobs found",
            "company": "",
            "location": location,
            "url": "",
            "score": 0,
            "created": ""
        }]
    return jobs

async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    session = get_session(user_id)
    email = update.message.text.strip()
    session["email"] = email

    jobs = session.get("jobs", [])
    skills = session.get("skills", [])
    save_user(user_id, email, skills)      # Save user info
    save_jobs(user_id, jobs)               # Save jobs one by one

    # Prepare job list for email
    job_lines = []
    for job in jobs:
        job_lines.append(
            f"{job['title']} at {job['company']} ({job['location']})\n"
            f"Apply: {job['url']}\n"
            f"Match Score: {job['score']}%\n"
        )
    job_text = "\n".join(job_lines) if job_lines else "No jobs found."

    # Send email 
    msg = MIMEText(job_text)
    msg["Subject"] = "Your CareerCue Job Recommendations"
    msg["From"] = "nayakshreyaravish@gmail.com"
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("nayakshreyaravish@gmail.com", "hqlpudsrsnxmotdd") 
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        await update.message.reply_text("✅ Job recommendations sent to your email!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send email: {e}")

    return ConversationHandler.END

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    session = get_session(user_id)
    if session and "bot_message_ids" in session:
        chat_id = update.effective_chat.id
        for msg_id in session["bot_message_ids"]:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass  # Ignore if message can't be deleted
    clear_session(user_id)
    await update.message.reply_text("🛑 Conversation stopped. To start again, type /start.")
    return ConversationHandler.END

async def send_and_track_message(update, session, text, **kwargs):
    msg = await update.message.reply_text(text, **kwargs)
    if session is not None:
        session.setdefault("bot_message_ids", []).append(msg.message_id)
    return msg

def skill_gap_analysis(user_skills, job_title):
    # Find the closest matching job role
    job_title_lower = job_title.lower()
    matched_role = None
    for role in JOB_ROLE_SKILLS:
        if role in job_title_lower:
            matched_role = role
            break
    if not matched_role:
        return None, []

    required_skills = JOB_ROLE_SKILLS[matched_role]
    user_skills_set = set([s.strip().lower() for s in user_skills])
    missing_skills = [skill for skill in required_skills if skill.lower() not in user_skills_set]
    return matched_role, missing_skills

# one-time instruction message shown before /start (for users who type messages without starting)
async def require_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # if user already started a session, do nothing
    if get_session(user_id):
        return

    # show instructions only once per user to avoid spam
    if has_shown_instructions(user_id):
        return

    # register visible bot commands (these appear in the client UI)
    try:
        await context.bot.set_my_commands([
            BotCommand("start", "Begin CareerCue"),
            BotCommand("stop", "Stop and clear bot messages"),
            BotCommand("help", "Show help / instructions"),
            BotCommand("skills", "Edit your skills"),
        ])
    except Exception:
        pass  # ignore if network fails

    keyboard = ReplyKeyboardMarkup([["/start", "/help", "/stop"]], resize_keyboard=True)
    instruction_text = (
        "👋 Welcome to CareerCue!\n\n"
        "If you're new, press /start to begin. You can stop at any time with /stop — this clears the bot's messages from the chat.\n\n"
        "Quick tips:\n"
        "• Upload your LinkedIn `.json` after /start\n"
        "• Use the big buttons below or type the commands\n"
        "• If you need help, press /help"
    )

    # send instruction message
    await update.message.reply_text(instruction_text, reply_markup=keyboard)
    mark_instructions_shown(user_id)

# Help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = get_session(user_id)

    help_text = (
        "🛠️ *CareerCue Bot - Help & Instructions*\n\n"
        "Welcome to CareerCue! This bot helps you find job opportunities based on your LinkedIn profile and preferred skills.\n\n"
        "Here's how to use the bot:\n"
        "1. Press /start to begin the job discovery process.\n"
        "2. Upload your LinkedIn `.json` profile file when prompted.\n"
        "3. Enter your preferred job location.\n"
        "4. Review and confirm the skills extracted from your profile.\n"
        "5. Optionally, add more skills or modify your details.\n"
        "6. Receive personalized job recommendations.\n"
        "7. Get job alerts and application links sent to your email.\n\n"
        "🔄 You can stop the bot at any time by pressing /stop. This will clear the bot's messages from the chat.\n\n"
        "✉️ For any issues or feedback, contact the bot administrator."
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler (define before app.add_handler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_JSON: [MessageHandler(filters.Document.ALL, receive_json)],
            ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_location)],
            ASK_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_skills)],
            ASK_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_details)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    # register visible commands in the client (so users see them in the UI)
    try:
        asyncio.get_event_loop().run_until_complete(
            app.bot.set_my_commands([
                BotCommand("start", "Begin CareerCue"),
                BotCommand("stop", "Stop and clear bot messages"),
                BotCommand("help", "Show instructions"),
                BotCommand("skills", "Edit your skills"),
            ])
        )
    except Exception:
        pass

    # add handlers, then run
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, require_start), group=1)

    print("🤖 CareerCue Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

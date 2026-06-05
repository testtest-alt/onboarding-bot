import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_IDS = [7884865944, 8924772643]

SECTIONS = [
    {
        "title": "📋 INTRODUCTION QUESTIONS",
        "questions": [
            "Can you briefly introduce yourself?",
            "What's your previous work or professional experience?",
            "Why are you interested in working as an OnlyFans DM handler?",
            "What do you understand about the day-to-day role of an OnlyFans chatter?",
            "How familiar are you with OnlyFans? Have you worked as a chatter, or in similar adult content messaging roles? If yes, how long for, how many accounts & what kind of results (e.g. upsells, renewals, revenue impact) did you achieve?",
        ],
    },
    {
        "title": "🎭 SCENARIO-BASED QUESTIONS\n\nShort creator profile:\n• 18 Years Old\n• Very playful and flirty\n• GFE Experience",
        "questions": [
            'A new subscriber messages: "Hey babe, I\'m really horny tonight. Tell me what you\'d do to me." How would you reply to build excitement and naturally lead toward a PPV or tip?',
            "A regular fan asks for a specific type of content or kink that the creator doesn't offer. How do you respond while keeping them subscribed and interested?",
            "Write a short welcome or renewal message for a subscriber that matches the creator's vibe and encourages engagement or spending.",
            "A fan goes quiet after a few flirty messages and hasn't replied in 2-3 days. How would you re-engage them without sounding desperate?",
            "A subscriber says they're not in a private place right now and can't engage fully. How would you respond while protecting value and encouraging a purchase later?",
            'A subscriber complains: "I\'ve been subscribed for a week and you barely message me, I\'m thinking of unsubscribing." How would you rebuild excitement and retention?',
            "A fan sends an unsolicited explicit photo and asks for an immediate reaction. How would you respond in a way that engages and potentially leads to a sale?",
            "A new or renewing subscriber shares personal details (e.g., stress, loneliness, hobbies). How would you build rapport and pivot back to engagement or a sale?",
            'A fan asks: "What are you wearing right now?" How would you respond in a way that builds intrigue and monetization potential?',
            "A subscriber complains that prices are too high. How would you justify value and still aim to convert them?",
        ],
    },
    {
        "title": "⚙️ RELIABILITY, PROFESSIONALISM & PERFORMANCE",
        "questions": [
            "What's your typing speed (words per minute)?",
            "Are you comfortable managing 10-30+ conversations simultaneously without mixing up fan details?",
            "How would you adapt your messaging style to match a specific creator's personality (e.g., innocent, dominant, playful, etc.)? Give a quick example.",
            "Are you willing to follow scripts/guidelines while still personalising replies, and strictly stay in character without breaking immersion?",
            "What's your weekly availability and preferred shift length? Can you commit to consistent hours (e.g., 8-12 hour shifts, 6-7 days per week)?",
            "Do you have a reliable workspace (quiet environment, stable internet, proper setup) with minimal distractions?",
        ],
    },
]

QUESTIONS = []
SECTION_MAP = {}

idx = 0
for section in SECTIONS:
    SECTION_MAP[idx] = section["title"]
    for q in section["questions"]:
        QUESTIONS.append(q)
        idx += 1

TOTAL = len(QUESTIONS)

GOODBYE = (
    "Thank you for your application.\n\n"
    "We appreciate you taking the time to apply. We will review your responses and get back "
    "to you shortly with an update on the next steps."
)

WELCOME = (
    "Hello! Thank you for your interest in joining our team.\n\n"
    "Before we begin, please note that this role is strictly for experienced chatters "
    "with excellent written English. If you do not have prior experience in this type of role "
    "or strong English skills, we kindly ask that you do not proceed with the application, "
    "as you will be wasting your time.\n\n"
    "Please also be aware that the use of AI to answer any questions is strictly prohibited "
    "and will be easily detected.\n\n"
    "Type /start whenever you're ready to begin."
)


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, step: int):
    prefix = ""
    if step in SECTION_MAP:
        prefix = f"\n{SECTION_MAP[step]}\n\n"
    q_text = f"{prefix}Q{step + 1} of {TOTAL}:\n{QUESTIONS[step]}"
    await update.message.reply_text(q_text)


async def forward_to_owner(context: ContextTypes.DEFAULT_TYPE, user):
    username = f"@{user.username}" if user.username else f"ID:{user.id}"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"

    logger.info(f"Attempting to forward application from {username}")

    lines = [
        "📥 NEW APPLICATION RECEIVED",
        f"Name: {full_name}",
        f"Username: {username}",
        f"User ID: {user.id}",
        "",
    ]

    for i, answer in enumerate(context.user_data["answers"]):
        if i in SECTION_MAP:
            lines.append(f"\n{SECTION_MAP[i]}\n")
        lines.append(f"Q{i + 1}: {QUESTIONS[i]}")
        lines.append(f"Answer: {answer}\n")

    message = "\n".join(lines)
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]

    try:
        for owner_id in OWNER_IDS:
            for chunk in chunks:
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=chunk
                )
        logger.info("Successfully forwarded application to all owners")
    except Exception as e:
        logger.error(f"Failed to send to owner: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["answers"] = []
    context.user_data["step"] = 0
    context.user_data["started"] = True
    await send_question(update, context, 0)


async def intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("started"):
        await update.message.reply_text("Type /start to begin your application.")
        return

    step = context.user_data["step"]

    if step >= TOTAL:
        await update.message.reply_text("You've already completed the application. Thank you!")
        return

    context.user_data["answers"].append(update.message.text)
    step += 1
    context.user_data["step"] = step

    if step < TOTAL:
        await send_question(update, context, step)
    else:
        context.user_data["started"] = False
        await update.message.reply_text(GOODBYE)
        await forward_to_owner(context, update.effective_user)


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", intro))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    print("Bot is running...")
    app.run_polling()

import telebot
import time
import threading
from queue import Queue
from openai import OpenAI
from openai import RateLimitError, APIError

# ======================
# KEYS
# ======================
TELEGRAM_TOKEN = "8862764456:AAEHchsavPHdXP2ucd0NSTuvnT3VZScgMjA"
OPENAI_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# ======================
# QUEUE SYSTEM (IMPORTANT)
# ======================
task_queue = Queue()

user_last_time = {}
COOLDOWN = 8  # seconds per user

# ======================
# START
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "📊 PRO Smart Money AI Bot Ready\n\nSend a chart or text for analysis."
    )

# ======================
# SAFE AI CALL
# ======================
def ask_ai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional Smart Money Concept trader. Analyze liquidity, BOS, CHoCH, FVG, market structure, and give entry/SL/TP."
                },
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content

    except RateLimitError:
        return "⚠ AI busy (rate limit). Try again in a few seconds."
    except APIError:
        return "⚠ OpenAI server error. Try again later."
    except Exception as e:
        return f"⚠ Error: {str(e)}"

# ======================
# WORKER (PRO QUEUE ENGINE)
# ======================
def worker():
    while True:
        message = task_queue.get()

        chat_id = message.chat.id
        text = message.text

        result = ask_ai(text)
        bot.send_message(chat_id, result)

        task_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

# ======================
# TEXT HANDLER (WITH COOLDOWN)
# ======================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    now = time.time()

    # cooldown protection
    if user_id in user_last_time:
        if now - user_last_time[user_id] < COOLDOWN:
            bot.send_message(message.chat.id, "⏳ Slow down. Wait a few seconds.")
            return

    user_last_time[user_id] = now

    task_queue.put(message)

# ======================
# RUN BOT
# ======================
print("🚀 PRO BOT RUNNING...")
bot.infinity_polling()
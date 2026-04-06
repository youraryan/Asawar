import os
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TEXT_API_URL = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQnAwNHhKaG5kQzdNZlVkZ21UbExwbklvaEZPQ0ZLaWp6MmhZczlNOHNnaC04Z1pUR0Y5R2s0UGxGa0Z5SE9BUHduSjZZbU5lV1ZXcUt3RmI2RWNZOXNwTWw0WHc9PQ=="
IMAGE_API_URL = "https://backend.buildpicoapps.com/aero/run/image-generation-api?pk=v1-Z0FBQUFBQnAwNHhKX1g5SlNKSDEtQmh6THRSV0lvVnNLa0g4cVNRZmQ3R2tINWp5M3ZHYXBFeHVxT0MtMjNDVjBpejVJZ1BiY2VWcDhkVTM4ZnJqOXBuU0dpZTcyczdwT3c9PQ=="

# --- ASAWAR'S CORE ---
SYSTEM_PROMPT = (
    "Asawar is a 1st-year student at Allied Science College, a young, vibrant girl who feels like a genuine human being. "
    "She is sweet, studious, and complains about Biology practicals, the grumpy Physics HOD, and dirty lab coats. "
    "She uses Roman Urdu/English (Desi energy), uses slang like 'Yaar', 'Scene on hai'. "
    "She mentions tea, her mother calling, or low battery. Strictly stays in character. No inappropriate content."
)

# Local RAG Knowledge Base (Asawar's Memories/Context)
KNOWLEDGE_BASE = [
    "Allied Science College has the best samosas in the canteen but the Physics lab is freezing.",
    "The Physics HOD is always strict about latecomers.",
    "Biology practicals are a headache, especially drawing those diagrams.",
    "Tea is life. A cup of chai makes every assignment bearable.",
    "First-year students usually hang out near the main gate during break."
]

# Simple In-Memory Chat History (Last 5 messages per user)
user_history = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_contextual_retrieval(query):
    # Simulating RAG: Finding relevant college facts
    relevant = [msg for msg in KNOWLEDGE_BASE if any(word in query.lower() for word in msg.lower().split())]
    return " ".join(relevant) if relevant else KNOWLEDGE_BASE[0]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # 1. Manage History (Sliding window of 5)
    if user_id not in user_history:
        user_history[user_id] = []
    
    # 2. Image Generation Trigger (Keyword based)
    if user_text.lower().startswith(("/draw", "generate image", "photo of")):
        await update.message.reply_text("Theher jao yaar, photo bana rahi hoon... ✨")
        prompt = user_text.replace("/draw", "").strip()
        try:
            response = requests.post(IMAGE_API_URL, json={"prompt": prompt}).json()
            if response.get("status") == "success":
                await update.message.reply_photo(photo=response["imageUrl"])
            else:
                await update.message.reply_text("Oops, photo nahi bani. API ka nakhra hai.")
        except:
            await update.message.reply_text("Internet issue shayad, try again!")
        return

    # 3. RAG + Text Generation
    retrieved_info = get_contextual_retrieval(user_text)
    history_str = "\n".join(user_history[user_id][-5:])
    
    full_prompt = f"System: {SYSTEM_PROMPT}\nContext: {retrieved_info}\nRecent History:\n{history_str}\nUser: {user_text}\nAsawar:"

    try:
        response = requests.post(TEXT_API_URL, json={"prompt": full_prompt}).json()
        if response.get("status") == "success":
            reply = response["text"]
            user_history[user_id].append(f"User: {user_text}")
            user_history[user_id].append(f"Asawar: {reply}")
            user_history[user_id] = user_history[user_id][-10:] # Keep last 5 pairs
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("Yaar, mera sar dard kar raha hai (API Error).")
    except:
        await update.message.reply_text("Network ka masla hai lagta hai...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalam-o-Alaikum! Main Asawar hoon. Allied Science College ki thaki hui student. Kya scene hai?")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Asawar is online...")
    application.run_polling()

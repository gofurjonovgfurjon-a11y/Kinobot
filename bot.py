import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *args):
        pass

threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), Handler).serve_forever(), daemon=True).start()

TOKEN = "8983129680:AAHOBTUA_wt4BJLckxqg-FR2hKcdv7iIX78"
MONGO_URI = "mongodb+srv://Kinobot:Agafurvv78@cluster0.dy9xrik.mongodb.net/?appName=Cluster0"
CHANNEL_ID = -1003932032419
CHANNEL_LINK = "https://t.me/+B6ntAmj86_AwOTUy"

client = MongoClient(MONGO_URI)
db = client["kinobot"]
col = db["movies"]

async def check_sub(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_sub(update.message.from_user.id, context.bot):
        keyboard = [[InlineKeyboardButton("📢 Kanalga obuna bo'ling", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Botdan foydalanish uchun kanalga obuna bo'ling!\n\nObuna bo'lgach /start bosing.",
            reply_markup=reply_markup
        )
        return
    await update.message.reply_text("🎬 KinoKashf ga xush kelibsiz!\n\nKino raqamini yozing!")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_sub(update.message.from_user.id, context.bot):
        keyboard = [[InlineKeyboardButton("📢 Kanalga obuna bo'ling", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Avval kanalga obuna bo'ling!",
            reply_markup=reply_markup
        )
        return
    text = update.message.text.strip()
    if text.startswith("/del "):
        code = text[5:]
        col.delete_one({"code": code})
        await update.message.reply_text(f"✅ {code} raqamli kino o'chirildi!")
        return
    movie = col.find_one({"code": text})
    if movie:
        keyboard = []
        if "q360" in movie:
            keyboard.append([InlineKeyboardButton("📱 360p", callback_data=f"{text}|360")])
        if "q720" in movie:
            keyboard.append([InlineKeyboardButton("🎬 720p", callback_data=f"{text}|720")])
        if "q1080" in movie:
            keyboard.append([InlineKeyboardButton("🔥 1080p", callback_data=f"{text}|1080")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🎬 {movie['name']}\n"
            f"📅 {movie['info']}\n"
            f"👥 {movie['actors']}\n"
            f"⭐ {movie['imdb']}\n"
            f"💰 {movie['budget']}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await check_sub(query.from_user.id, context.bot):
        keyboard = [[InlineKeyboardButton("📢 Kanalga obuna bo'ling", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("⚠️ Avval kanalga obuna bo'ling!", reply_markup=reply_markup)
        return
    code, quality = query.data.split("|")
    movie = col.find_one({"code": code})
    file_id = movie[f"q{quality}"]
    await query.message.reply_video(file_id)

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video and update.message.caption:
        parts = update.message.caption.split("|")
        if len(parts) == 7:
            code, name, info, actors, imdb, budget, quality = parts
            col.update_one(
                {"code": code},
                {"$set": {
                    "code": code,
                    "name": name,
                    "info": info,
                    "actors": actors,
                    "imdb": imdb,
                    "budget": budget,
                    f"q{quality}": update.message.video.file_id
                }},
                upsert=True
            )
            await update.message.reply_text(f"✅ {name} ({quality}) saqlandi!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.VIDEO, save))
app.add_handler(MessageHandler(filters.TEXT, handle))
app.run_polling()

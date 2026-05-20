import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
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

def load_movies():
    if os.path.exists("movies.json"):
        with open("movies.json", "r") as f:
            return json.load(f)
    return {}

def save_movies(movies):
    with open("movies.json", "w") as f:
        json.dump(movies, f)

movies = load_movies()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 KinoKashf ga xush kelibsiz!\n\nKino raqamini yozing!")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("/del "):
        code = text[5:]
        if code in movies:
            del movies[code]
            save_movies(movies)
            await update.message.reply_text(f"✅ {code} raqamli kino o'chirildi!")
        else:
            await update.message.reply_text("❌ Bunday kino topilmadi!")
        return
    if text in movies:
        movie = movies[text]
        keyboard = []
        if "360" in movie:
            keyboard.append([InlineKeyboardButton("📱 360p", callback_data=f"{text}|360")])
        if "720" in movie:
            keyboard.append([InlineKeyboardButton("🎬 720p", callback_data=f"{text}|720")])
        if "1080" in movie:
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
    code, quality = query.data.split("|")
    file_id = movies[code][quality]
    await query.message.reply_video(file_id)

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video and update.message.caption:
        parts = update.message.caption.split("|")
        if len(parts) == 7:
            code, name, info, actors, imdb, budget, quality = parts
            if code not in movies:
                movies[code] = {
                    "name": name,
                    "info": info,
                    "actors": actors,
                    "imdb": imdb,
                    "budget": budget
                }
            movies[code][quality] = update.message.video.file_id
            save_movies(movies)
            await update.message.reply_text(f"✅ {name} ({quality}) saqlandi!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.VIDEO, save))
app.add_handler(MessageHandler(filters.TEXT, handle))
app.run_polling()

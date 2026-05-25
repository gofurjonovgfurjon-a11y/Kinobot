import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ── HTTP server (Render uchun) ──────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *args):
        pass

threading.Thread(
    target=lambda: HTTPServer(('0.0.0.0', 8080), Handler).serve_forever(),
    daemon=True
).start()

# ── Token ───────────────────────────────────────────────────────────────────
TOKEN = "8983129680:AAHOBTUA_wt4BJLckxqg-FR2hKcdv7iIX78"

# ── Admin ID (o'zingizning Telegram ID ingizni yozing) ──────────────────────
ADMIN_ID = 123456789  # <-- O'zgartiring!

# ── Ma'lumotlarni yuklash/saqlash ───────────────────────────────────────────
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

movies = load_data("movies.json")      # {kod: {name, info, 360, 720, 1080}}
worlds = load_data("worlds.json")      # {olam_nomi: [kod1, kod2, ...]}

# ── Asosiy menyu ────────────────────────────────────────────────────────────
def main_menu():
    keyboard = [
        [KeyboardButton("🔍 Kino qidirish")],
        [KeyboardButton("📋 Barcha kinolar")],
        [KeyboardButton("🌌 Kino olamlar")],
        [KeyboardButton("📞 Admin bilan bog'lanish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🎬 *KinoBot ga xush kelibsiz!*\n\nQuyidagi menyudan tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ── Asosiy matn handler ──────────────────────────────────────────────────────
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    state = context.user_data.get("state", "")
    user_id = update.effective_user.id

    # ── Admin: kino o'chirish ─────────────────────────────────────────────
    if text.startswith("/del ") and user_id == ADMIN_ID:
        code = text[5:].strip()
        if code in movies:
            del movies[code]
            save_data("movies.json", movies)
            await update.message.reply_text(f"✅ {code} raqamli kino o'chirildi!")
        else:
            await update.message.reply_text("❌ Bunday kino topilmadi!")
        return

    # ── Admin: olam yaratish ──────────────────────────────────────────────
    if text.startswith("/newworld ") and user_id == ADMIN_ID:
        world_name = text[10:].strip()
        if world_name not in worlds:
            worlds[world_name] = []
            save_data("worlds.json", worlds)
            await update.message.reply_text(f"✅ '{world_name}' olami yaratildi!")
        else:
            await update.message.reply_text("⚠️ Bu olam allaqachon mavjud!")
        return

    # ── Admin: olamga kino qo'shish ───────────────────────────────────────
    # /addtoworld OlamNomi|KinoKod
    if text.startswith("/addtoworld ") and user_id == ADMIN_ID:
        parts = text[12:].strip().split("|")
        if len(parts) == 2:
            world_name, code = parts[0].strip(), parts[1].strip()
            if world_name in worlds and code in movies:
                if code not in worlds[world_name]:
                    worlds[world_name].append(code)
                    save_data("worlds.json", worlds)
                    await update.message.reply_text(f"✅ {movies[code]['name']} → '{world_name}' olamiga qo'shildi!")
                else:
                    await update.message.reply_text("⚠️ Bu kino allaqachon bu olamda bor!")
            else:
                await update.message.reply_text("❌ Olam yoki kino topilmadi!")
        else:
            await update.message.reply_text("❗ Format: /addtoworld OlamNomi|KinoKod")
        return

    # ── Admin: olamdan kino o'chirish ─────────────────────────────────────
    # /delfromworld OlamNomi|KinoKod
    if text.startswith("/delfromworld ") and user_id == ADMIN_ID:
        parts = text[14:].strip().split("|")
        if len(parts) == 2:
            world_name, code = parts[0].strip(), parts[1].strip()
            if world_name in worlds and code in worlds[world_name]:
                worlds[world_name].remove(code)
                save_data("worlds.json", worlds)
                await update.message.reply_text(f"✅ Kino '{world_name}' olamidan o'chirildi!")
            else:
                await update.message.reply_text("❌ Topilmadi!")
        return

    # ── Menyu tugmalari ───────────────────────────────────────────────────
    if text == "🔍 Kino qidirish":
        context.user_data["state"] = "search"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔤 Nomi bo'yicha", callback_data="search_name")],
            [InlineKeyboardButton("🔢 Kod bo'yicha", callback_data="search_code")],
        ])
        await update.message.reply_text("Qidiruv turini tanlang:", reply_markup=kb)
        return

    if text == "📋 Barcha kinolar":
        await show_all_movies(update, context)
        return

    if text == "🌌 Kino olamlar":
        await show_worlds(update, context)
        return

    if text == "📞 Admin bilan bog'lanish":
        await update.message.reply_text("📩 Admin: @admin_username")
        return

    # ── Qidiruv holati ────────────────────────────────────────────────────
    if state == "search_by_name":
        results = {k: v for k, v in movies.items() if text.lower() in v.get("name", "").lower()}
        if results:
            for code, movie in results.items():
                kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"🎬 {movie['name']}", callback_data=f"movie|{code}")]])
                await update.message.reply_text(f"🎬 *{movie['name']}*\n📝 {movie.get('info','')}", parse_mode="Markdown", reply_markup=kb)
        else:
            await update.message.reply_text("❌ Kino topilmadi!")
        context.user_data["state"] = ""
        return

    if state == "search_by_code":
        if text in movies:
            await send_movie_menu(update, text)
        else:
            await update.message.reply_text("❌ Kino topilmadi!")
        context.user_data["state"] = ""
        return

    # ── Oddiy kod kiritish (eski usul ham ishlaydi) ───────────────────────
    if text in movies:
        await send_movie_menu(update, text, message=update.message)
        return

    await update.message.reply_text("❓ Nima qilishni bilmadim. Menyudan tanlang:", reply_markup=main_menu())

# ── Barcha kinolar ro'yxati ──────────────────────────────────────────────────
async def show_all_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not movies:
        await update.message.reply_text("📭 Hech qanday kino yo'q!")
        return
    buttons = []
    for code, movie in movies.items():
        buttons.append([InlineKeyboardButton(f"🎬 {movie['name']} [{code}]", callback_data=f"movie|{code}")])
    kb = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("📋 *Barcha kinolar:*", parse_mode="Markdown", reply_markup=kb)

# ── Kino olamlar ─────────────────────────────────────────────────────────────
async def show_worlds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not worlds:
        await update.message.reply_text("🌌 Hozircha hech qanday olam yo'q!")
        return
    buttons = []
    for world_name in worlds.keys():
        buttons.append([InlineKeyboardButton(f"🌌 {world_name}", callback_data=f"world|{world_name}")])
    kb = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("🌌 *Kino olamlarini tanlang:*", parse_mode="Markdown", reply_markup=kb)

# ── Kino menyu (sifat tanlash) ───────────────────────────────────────────────
async def send_movie_menu(update, code, message=None):
    movie = movies[code]
    keyboard = []
    if "360" in movie:
        keyboard.append([InlineKeyboardButton("📱 360p", callback_data=f"quality|{code}|360")])
    if "720" in movie:
        keyboard.append([InlineKeyboardButton("🎬 720p", callback_data=f"quality|{code}|720")])
    if "1080" in movie:
        keyboard.append([InlineKeyboardButton("🔥 1080p", callback_data=f"quality|{code}|1080")])
    kb = InlineKeyboardMarkup(keyboard)
    msg = message or update.message
    await msg.reply_text(
        f"🎬 *{movie['name']}*\n📝 {movie.get('info', '')}",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ── Callback handler ──────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Sifat tanlash → video yuborish
    if data.startswith("quality|"):
        _, code, quality = data.split("|")
        if code in movies and quality in movies[code]:
            await query.message.reply_video(movies[code][quality])
        return

    # Kino tanlash (ro'yxatdan)
    if data.startswith("movie|"):
        code = data.split("|")[1]
        if code in movies:
            await send_movie_menu(query, code, message=query.message)
        return

    # Olam tanlash
    if data.startswith("world|"):
        world_name = data.split("|", 1)[1]
        codes = worlds.get(world_name, [])
        if not codes:
            await query.message.reply_text(f"🌌 '{world_name}' olamida hali kino yo'q!")
            return
        buttons = []
        for code in codes:
            if code in movies:
                buttons.append([InlineKeyboardButton(f"🎬 {movies[code]['name']}", callback_data=f"movie|{code}")])
        kb = InlineKeyboardMarkup(buttons)
        await query.message.reply_text(f"🌌 *{world_name}* olamidagi kinolar:", parse_mode="Markdown", reply_markup=kb)
        return

    # Qidiruv turi
    if data == "search_name":
        context.user_data["state"] = "search_by_name"
        await query.message.reply_text("🔤 Kino nomini yozing:")
        return

    if data == "search_code":
        context.user_data["state"] = "search_by_code"
        await query.message.reply_text("🔢 Kino kodini yozing:")
        return

# ── Video yuklash (admin) ─────────────────────────────────────────────────────
# Caption formati: kod|nomi|info|sifat
# Masalan: 001|Avengers|Marvel filmi|720
async def save_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    if update.message.video and update.message.caption:
        parts = update.message.caption.split("|")
        if len(parts) == 4:
            code, name, info, quality = [p.strip() for p in parts]
            if code not in movies:
                movies[code] = {"name": name, "info": info}
            movies[code][quality] = update.message.video.file_id
            save_data("movies.json", movies)
            await update.message.reply_text(f"✅ *{name}* ({quality}) saqlandi! Kod: `{code}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❗ Format: kod|nomi|info|sifat\nMasalan: 001|Avengers|Marvel filmi|720")

# ── Admin yordam ─────────────────────────────────────────────────────────────
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = (
        "🛠 *Admin buyruqlari:*\n\n"
        "📤 *Kino yuklash:* Video yuboring, caption:\n`kod|nomi|info|sifat`\n\n"
        "🗑 *Kino o'chirish:*\n`/del KOD`\n\n"
        "🌌 *Olam yaratish:*\n`/newworld OlamNomi`\n\n"
        "➕ *Olamga kino qo'shish:*\n`/addtoworld OlamNomi|KinoKod`\n\n"
        "➖ *Olamdan kino o'chirish:*\n`/delfromworld OlamNomi|KinoKod`\n\n"
        "📋 *Mavjud olamlar:*\n`/listworlds`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_worlds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not worlds:
        await update.message.reply_text("Hech qanday olam yo'q!")
        return
    text = "🌌 *Mavjud olamlar:*\n\n"
    for name, codes in worlds.items():
        text += f"• *{name}*: {len(codes)} ta kino\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ── App ──────────────────────────────────────────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_help))
app.add_handler(CommandHandler("listworlds", list_worlds))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.VIDEO, save_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.run_polling()

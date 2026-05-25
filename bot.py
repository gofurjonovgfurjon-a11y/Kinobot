import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ChatJoinRequestHandler, filters, ContextTypes

# ── HTTP server (Render uchun) ──────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *args):
        pass

threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), Handler).serve_forever(), daemon=True).start()

# ── Sozlamalar ───────────────────────────────────────────────────────────────
TOKEN = "8983129680:AAHOBTUA_wt4BJLckxqg-FR2hKcdv7iIX78"
MONGO_URI = "mongodb+srv://Kinobot:Agafurvv78@cluster0.dy9xrik.mongodb.net/?appName=Cluster0"
CHANNEL_ID = -1003932032419
CHANNEL_LINK = "https://t.me/+B6ntAmj86_AwOTUy"
ADMIN_ID = 7045504375

# ── MongoDB ──────────────────────────────────────────────────────────────────
client = MongoClient(MONGO_URI)
db = client["kinobot"]
col = db["movies"]
worlds_col = db["worlds"]

# ── Obuna tekshirish ─────────────────────────────────────────────────────────
async def check_sub(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ── Obuna tugmasi ────────────────────────────────────────────────────────────
def sub_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_sub")]
    ])

# ── Asosiy menyu ────────────────────────────────────────────────────────────
def main_menu():
    keyboard = [
        [KeyboardButton("🔍 Kino qidirish")],
        [KeyboardButton("📋 Barcha kinolar")],
        [KeyboardButton("🌌 Kino olamlar")],
        [KeyboardButton("📞 Admin bilan bog'lanish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ── Join request ─────────────────────────────────────────────────────────────
async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.chat_join_request.approve()
    await context.bot.send_message(
        update.chat_join_request.from_user.id,
        "✅ Kanalga qo'shildingiz!\n\n🎬 KinoKashf ga xush kelibsiz!",
        reply_markup=main_menu()
    )

# ── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_sub(user_id, context.bot):
        await update.message.reply_text(
            "⚠️ Botdan foydalanish uchun kanalga qo'shiling!\n\nQo'shilgach ✅ Tasdiqlash bosing.",
            reply_markup=sub_keyboard()
        )
        return
    context.user_data.clear()
    await update.message.reply_text(
        "🎬 *KinoKashf ga xush kelibsiz!*\n\nKino raqamini yozing yoki menyudan tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ── Kino ma'lumotlarini ko'rsatish ───────────────────────────────────────────
async def show_movie(message, movie):
    keyboard = []
    if "q360" in movie:
        keyboard.append([InlineKeyboardButton("📱 360p", callback_data=f"{movie['code']}|360")])
    if "q720" in movie:
        keyboard.append([InlineKeyboardButton("🎬 720p", callback_data=f"{movie['code']}|720")])
    if "q1080" in movie:
        keyboard.append([InlineKeyboardButton("🔥 1080p", callback_data=f"{movie['code']}|1080")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = (
        f"🎬 {movie['name']}\n"
        f"📅 {movie.get('info', '')}\n"
        f"👥 {movie.get('actors', '')}\n"
        f"⭐ {movie.get('imdb', '')}\n"
        f"💰 {movie.get('budget', '')}"
    )
    if "trailer" in movie:
        await message.reply_video(movie["trailer"], caption=caption, reply_markup=reply_markup)
    else:
        await message.reply_text(caption, reply_markup=reply_markup)

# ── Barcha kinolar ───────────────────────────────────────────────────────────
async def show_all_movies(update: Update):
    all_movies = list(col.find())
    if not all_movies:
        await update.message.reply_text("📭 Hech qanday kino yo'q!")
        return
    buttons = []
    for movie in all_movies:
        buttons.append([InlineKeyboardButton(
            f"🎬 {movie['name']} [{movie['code']}]",
            callback_data=f"movie|{movie['code']}"
        )])
    await update.message.reply_text(
        "📋 *Barcha kinolar:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ── Kino olamlar ─────────────────────────────────────────────────────────────
async def show_worlds(update: Update):
    all_worlds = list(worlds_col.find())
    if not all_worlds:
        await update.message.reply_text("🌌 Hozircha hech qanday olam yo'q!")
        return
    buttons = []
    for w in all_worlds:
        buttons.append([InlineKeyboardButton(f"🌌 {w['name']}", callback_data=f"world|{w['name']}")])
    await update.message.reply_text(
        "🌌 *Kino olamlarini tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ── Asosiy matn handler ──────────────────────────────────────────────────────
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = context.user_data.get("state", "")

    # Obuna tekshirish
    if not await check_sub(user_id, context.bot):
        await update.message.reply_text("⚠️ Avval kanalga qo'shiling!", reply_markup=sub_keyboard())
        return

    # ── Admin buyruqlari ──────────────────────────────────────────────────
    if user_id == ADMIN_ID:

        if text.startswith("/del "):
            code = text[5:].strip()
            movie = col.find_one({"code": code})
            if movie:
                col.delete_one({"code": code})
                await update.message.reply_text(f"✅ *{movie['name']}* o'chirildi!", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Kino topilmadi!")
            return

        if text.startswith("/newworld "):
            world_name = text[10:].strip()
            if not worlds_col.find_one({"name": world_name}):
                worlds_col.insert_one({"name": world_name, "movies": []})
                await update.message.reply_text(f"✅ *{world_name}* olami yaratildi!", parse_mode="Markdown")
            else:
                await update.message.reply_text("⚠️ Bu olam allaqachon mavjud!")
            return

        if text.startswith("/addtoworld "):
            parts = text[12:].strip().split("|")
            if len(parts) == 2:
                world_name, code = parts[0].strip(), parts[1].strip()
                world = worlds_col.find_one({"name": world_name})
                movie = col.find_one({"code": code})
                if world and movie:
                    worlds_col.update_one({"name": world_name}, {"$addToSet": {"movies": code}})
                    await update.message.reply_text(
                        f"✅ *{movie['name']}* → *{world_name}* olamiga qo'shildi!",
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text("❌ Olam yoki kino topilmadi!")
            else:
                await update.message.reply_text("❗ Format: /addtoworld OlamNomi|KinoKod")
            return

        if text.startswith("/delfromworld "):
            parts = text[14:].strip().split("|")
            if len(parts) == 2:
                world_name, code = parts[0].strip(), parts[1].strip()
                worlds_col.update_one({"name": world_name}, {"$pull": {"movies": code}})
                await update.message.reply_text(f"✅ Kino *{world_name}* olamidan o'chirildi!", parse_mode="Markdown")
            return

        if text.startswith("/delworld "):
            world_name = text[10:].strip()
            worlds_col.delete_one({"name": world_name})
            await update.message.reply_text(f"✅ *{world_name}* olami o'chirildi!", parse_mode="Markdown")
            return

    # ── Menyu tugmalari ───────────────────────────────────────────────────
    if text == "🔍 Kino qidirish":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔤 Nomi bo'yicha", callback_data="search_name")],
            [InlineKeyboardButton("🔢 Kod bo'yicha", callback_data="search_code")],
        ])
        await update.message.reply_text("Qidiruv turini tanlang:", reply_markup=kb)
        return

    if text == "📋 Barcha kinolar":
        await show_all_movies(update)
        return

    if text == "🌌 Kino olamlar":
        await show_worlds(update)
        return

    if text == "📞 Admin bilan bog'lanish":
        await update.message.reply_text("📩 Admin: @KinoKashf_admin")
        return

    # ── Qidiruv holati ────────────────────────────────────────────────────
    if state == "search_by_name":
        context.user_data["state"] = ""
        results = list(col.find({"name": {"$regex": text, "$options": "i"}}))
        if results:
            buttons = []
            for movie in results:
                buttons.append([InlineKeyboardButton(f"🎬 {movie['name']}", callback_data=f"movie|{movie['code']}")])
            await update.message.reply_text(
                f"🔍 *'{text}'* bo'yicha natijalar:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await update.message.reply_text("❌ Kino topilmadi!")
        return

    if state == "search_by_code":
        context.user_data["state"] = ""
        movie = col.find_one({"code": text})
        if not movie:
            try:
                movie = col.find_one({"code": int(text)})
            except:
                pass
        if movie:
            await show_movie(update.message, movie)
        else:
            await update.message.reply_text("❌ Kino topilmadi!")
        return

    # ── Oddiy kod kiritish ────────────────────────────────────────────────
    movie = col.find_one({"code": text})
    if not movie:
        try:
            movie = col.find_one({"code": int(text)})
        except:
            pass
    if movie:
        await show_movie(update.message, movie)
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

# ── Callback handler ──────────────────────────────────────────────────────────
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Obuna tekshirish
    if data == "check_sub":
        if await check_sub(query.from_user.id, context.bot):
            await query.message.edit_text(
                "🎬 KinoKashf ga xush kelibsiz!\n\nKino raqamini yozing yoki menyudan tanlang:"
            )
            await context.bot.send_message(query.from_user.id, "Menyudan tanlang:", reply_markup=main_menu())
        else:
            await query.answer("❌ Siz hali kanalga qo'shilmadingiz!", show_alert=True)
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

    # Barcha kinolar ro'yxatidan kino tanlash
    if data.startswith("movie|"):
        code = data.split("|")[1]
        movie = col.find_one({"code": code})
        if movie:
            await show_movie(query.message, movie)
        return

    # Olam tanlash
    if data.startswith("world|"):
        world_name = data.split("|", 1)[1]
        world = worlds_col.find_one({"name": world_name})
        if not world or not world.get("movies"):
            await query.message.reply_text(f"🌌 *{world_name}* olamida hali kino yo'q!", parse_mode="Markdown")
            return
        buttons = []
        for code in world["movies"]:
            movie = col.find_one({"code": code})
            if movie:
                buttons.append([InlineKeyboardButton(f"🎬 {movie['name']}", callback_data=f"movie|{code}")])
        if buttons:
            await query.message.reply_text(
                f"🌌 *{world_name}* olamidagi kinolar:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await query.message.reply_text(f"🌌 *{world_name}* olamida hali kino yo'q!", parse_mode="Markdown")
        return

    # Sifat tanlash → video yuborish
    if "|" in data:
        parts = data.split("|")
        if len(parts) == 2:
            code, quality = parts
            movie = col.find_one({"code": code})
            if movie and f"q{quality}" in movie:
                await query.message.reply_video(movie[f"q{quality}"])
        return

# ── Video yuklash (admin) ─────────────────────────────────────────────────────
async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    if update.message.video and update.message.caption:
        parts = update.message.caption.split("|")
        # Treyler: trailer|kod|nomi|yil|aktyorlar|imdb|byudjet
        if len(parts) == 7 and parts[0].strip().lower() == "trailer":
            _, code, name, info, actors, imdb, budget = [p.strip() for p in parts]
            col.update_one(
                {"code": code},
                {"$set": {"code": code, "name": name, "info": info, "actors": actors, "imdb": imdb, "budget": budget, "trailer": update.message.video.file_id}},
                upsert=True
            )
            await update.message.reply_text(f"✅ *{name}* treyleri saqlandi! Kod: `{code}`", parse_mode="Markdown")
        # Kino: kod|nomi|yil|aktyorlar|imdb|byudjet|sifat
        elif len(parts) == 7:
            code, name, info, actors, imdb, budget, quality = [p.strip() for p in parts]
            col.update_one(
                {"code": code},
                {"$set": {"code": code, "name": name, "info": info, "actors": actors, "imdb": imdb, "budget": budget, f"q{quality}": update.message.video.file_id}},
                upsert=True
            )
            await update.message.reply_text(f"✅ *{name}* ({quality}p) saqlandi! Kod: `{code}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "❗ Format:\n"
                "Kino: `kod|nomi|yil,rejissor|aktyorlar|IMDb|kassa|sifat`\n"
                "Treyler: `trailer|kod|nomi|yil,rejissor|aktyorlar|IMDb|kassa`",
                parse_mode="Markdown"
            )

# ── Admin yordam ─────────────────────────────────────────────────────────────
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = (
        "🛠 *Admin buyruqlari:*\n\n"
        "📤 *Kino yuklash:*\n`kod|nomi|yil,rejissor|aktyorlar|IMDb|kassa|sifat`\n\n"
        "🎞 *Treyler yuklash:*\n`trailer|kod|nomi|yil,rejissor|aktyorlar|IMDb|kassa`\n\n"
        "🗑 *Kino o'chirish:*\n`/del KOD`\n\n"
        "🌌 *Olam yaratish:*\n`/newworld OlamNomi`\n\n"
        "➕ *Olamga kino qo'shish:*\n`/addtoworld OlamNomi|KinoKod`\n\n"
        "➖ *Olamdan kino o'chirish:*\n`/delfromworld OlamNomi|KinoKod`\n\n"
        "🗑 *Olamni o'chirish:*\n`/delworld OlamNomi`\n\n"
        "📋 *Olamlar ro'yxati:*\n`/listworlds`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_worlds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    all_worlds = list(worlds_col.find())
    if not all_worlds:
        await update.message.reply_text("Hech qanday olam yo'q!")
        return
    text = "🌌 *Mavjud olamlar:*\n\n"
    for w in all_worlds:
        text += f"• *{w['name']}*: {len(w.get('movies', []))} ta kino\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ── App ──────────────────────────────────────────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(ChatJoinRequestHandler(approve_join))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_help))
app.add_handler(CommandHandler("listworlds", list_worlds))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.VIDEO, save))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling(drop_pending_updates=True)

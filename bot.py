import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ChatJoinRequestHandler, filters, ContextTypes

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
ADMIN_ID = 7045504375

client = MongoClient(MONGO_URI)
db = client["kinobot"]
col = db["movies"]
worlds_col = db["worlds"]

async def check_sub(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def sub_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_sub")]
    ])

def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔍 Kino qidirish")],
        [KeyboardButton("📋 Barcha kinolar")],
        [KeyboardButton("🌌 Kino olamlar")],
        [KeyboardButton("📞 Admin bilan bog'lanish")],
    ], resize_keyboard=True)

async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.chat_join_request.approve()
    await context.bot.send_message(
        update.chat_join_request.from_user.id,
        "✅ Kanalga qo'shildingiz!\n\n🎬 KinoKashf ga xush kelibsiz!",
        reply_markup=main_menu()
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_sub(update.message.from_user.id, context.bot):
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

async def show_movie(message, movie):
    keyboard = []
    if "q360" in movie:
        keyboard.append([InlineKeyboardButton("📱 360p", callback_data=f"{movie['code']}|360")])
    if "q720" in movie:
        keyboard.append([InlineKeyboardButton("🎬 720p", callback_data=f"{movie['code']}|720")])
    if "q1080" in movie:
        keyboard.append([InlineKeyboardButton("🔥 1080p", callback_data=f"{movie['code']}|1080")])
    caption = (
        f"🎬 {movie['name']}\n"
        f"📅 {movie.get('info', '')}\n"
        f"👥 {movie.get('actors', '')}\n"
        f"⭐ {movie.get('imdb', '')}\n"
        f"💰 {movie.get('budget', '')}"
    )
    if "trailer" in movie:
        await message.reply_video(movie["trailer"], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_all_movies(update: Update):
    all_movies = list(col.find())
    if not all_movies:
        await update.message.reply_text("📭 Hech qanday kino yo'q!")
        return
    buttons = [[InlineKeyboardButton(f"🎬 {m['name']} [{m['code']}]", callback_data=f"movie|{m['code']}")] for m in all_movies]
    await update.message.reply_text("📋 *Barcha kinolar:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

async def show_worlds(update: Update):
    all_worlds = list(worlds_col.find())
    if not all_worlds:
        await update.message.reply_text("🌌 Hozircha hech qanday olam yo'q!")
        return
    buttons = [[InlineKeyboardButton(f"🌌 {w['name']}", callback_data=f"world|{w['name']}")] for w in all_worlds]
    await update.message.reply_text("🌌 *Kino olamlarini tanlang:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = context.user_data.get("state", "")

    if not await check_sub(user_id, context.bot):
        await update.message.reply_text("⚠️ Avval kanalga qo'shiling!", reply_markup=sub_keyboard())
        return

    if text == "🔍 Kino qidirish":
        await update.message.reply_text("Qidiruv turini tanlang:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔤 Nomi bo'yicha", callback_data="search_name")],
            [InlineKeyboardButton("🔢 Kod bo'yicha", callback_data="search_code")],
        ]))
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

    if state == "search_by_name":
        context.user_data["state"] = ""
        results = list(col.find({"name": {"$regex": text, "$options": "i"}}))
        if results:
            buttons = [[InlineKeyboardButton(f"🎬 {m['name']}", callback_data=f"movie|{m['code']}")] for m in results]
            await update.message.reply_text(f"🔍 *'{text}'* bo'yicha:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.message.reply_text("❌ Kino topilmadi!")
        return

    if state == "search_by_code":
        context.user_data["state"] = ""
        movie = col.find_one({"code": text})
        if movie:
            await show_movie(update.message, movie)
        else:
            await update.message.reply_text("❌ Kino topilmadi!")
        return

    movie = col.find_one({"code": text})
    if movie:
        await show_movie(update.message, movie)
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "check_sub":
        if await check_sub(query.from_user.id, context.bot):
            await query.message.edit_text("🎬 KinoKashf ga xush kelibsiz!")
            await context.bot.send_message(query.from_user.id, "Menyudan tanlang:", reply_markup=main_menu())
        else:
            await query.answer("❌ Hali kanalga qo'shilmadingiz!", show_alert=True)
        return

    if data == "search_name":
        context.user_data["state"] = "search_by_name"
        await query.message.reply_text("🔤 Kino nomini yozing:")
        return

    if data == "search_code":
        context.user_data["state"] = "search_by_code"
        await query.message.reply_text("🔢 Kino kodini yozing:")
        return

    if data.startswith("movie|"):
        code = data.split("|")[1]
        movie = col.find_one({"code": code})
        if movie:
            await show_movie(query.message, movie)
        return

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
            await query.message.reply_text(f"🌌 *{world_name}* olamidagi kinolar:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await query.message.reply_text(f"🌌 *{world_name}* olamida hali kino yo'q!", parse_mode="Markdown")
        return

    if "|" in data:
        parts = data.split("|")
        if len(parts) == 2:
            code, quality = parts
            movie = col.find_one({"code": code})
            if movie and f"q{quality}" in movie:
                await query.message.reply_video(movie[f"q{quality}"])
        return

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    if update.message.video and update.message.caption:
        parts = update.message.caption.split("|")
        if len(parts) == 7 and parts[0].strip().lower() == "trailer":
            _, code, name, info, actors, imdb, budget = [p.strip() for p in parts]
            col.update_one({"code": code}, {"$set": {"code": code, "name": name, "info": info, "actors": actors, "imdb": imdb, "budget": budget, "trailer": update.message.video.file_id}}, upsert=True)
            await update.message.reply_text(f"✅ *{name}* treyleri saqlandi! Kod: `{code}`", parse_mode="Markdown")
        elif len(parts) == 7:
            code, name, info, actors, imdb, budget, quality = [p.strip() for p in parts]
            col.update_one({"code": code}, {"$set": {"code": code, "name": name, "info": info, "actors": actors, "imdb": imdb, "budget": budget, f"q{quality}": update.message.video.file_id}}, upsert=True)
            await update.message.reply_text(f"✅ *{name}* ({quality}p) saqlandi! Kod: `{code}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❗ {len(parts)} ta maydon. Format:\n`kod|nomi|yil,rejissor|aktyorlar|IMDb|kassa|sifat`", parse_mode="Markdown")

async def cmd_newworld(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    world_name = " ".join(context.args).strip()
    if not world_name:
        await update.message.reply_text("❗ Format: /newworld OlamNomi")
        return
    if not worlds_col.find_one({"name": world_name}):
        worlds_col.insert_one({"name": world_name, "movies": []})
        await update.message.reply_text(f"✅ *{world_name}* olami yaratildi!", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Bu olam allaqachon mavjud!")

async def cmd_addtoworld(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = " ".join(context.args)
    parts = args.split("|")
    if len(parts) == 2:
        world_name, code = parts[0].strip(), parts[1].strip()
        world = worlds_col.find_one({"name": world_name})
        movie = col.find_one({"code": code})
        if world and movie:
            worlds_col.update_one({"name": world_name}, {"$addToSet": {"movies": code}})
            await update.message.reply_text(f"✅ *{movie['name']}* → *{world_name}* olamiga qo'shildi!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Olam yoki kino topilmadi!")
    else:
        await update.message.reply_text("❗ Format: /addtoworld OlamNomi|KinoKod")

async def cmd_delfromworld(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = " ".join(context.args)
    parts = args.split("|")
    if len(parts) == 2:
        worlds_col.update_one({"name": parts[0].strip()}, {"$pull": {"movies": parts[1].strip()}})
        await update.message.reply_text("✅ Kino olamdan o'chirildi!")

async def cmd_delworld(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    world_name = " ".join(context.args).strip()
    worlds_col.delete_one({"name": world_name})
    await update.message.reply_text(f"✅ *{world_name}* olami o'chirildi!", parse_mode="Markdown")

async def cmd_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    code = " ".join(context.args).strip()
    movie = col.find_one({"code": code})
    if movie:
        col.delete_one({"code": code})
        await update.message.reply_text(f"✅ *{movie['name']}* o'chirildi!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Kino topilmadi!")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🛠 *Admin buyruqlari:*\n\n"
        "📤 *Kino yuklash:*\n`kod|nomi|yil,rejissor|aktyorlar|IMDb|kassa|sifat`\n"
        "📌 Masalan:\n`01|Kapitan Amerika|2011, Joe Johnston|Chris Evans...|IMDb: 6.9|$370 mln|720`\n\n"
        "🎞 *Treyler:*\n`trailer|kod|nomi|yil,rejissor|aktyorlar|IMDb|kassa`\n\n"
        "🌌 *Olam yaratish:*\n`/newworld Marvel Kino Olami`\n\n"
        "➕ *Olamga kino:*\n`/addtoworld Marvel Kino Olami|01`\n\n"
        "➖ *Olamdan o'chirish:*\n`/delfromworld Marvel Kino Olami|01`\n\n"
        "🗑 *Olamni o'chirish:*\n`/delworld OlamNomi`\n\n"
        "🗑 *Kinoni o'chirish:*\n`/del KOD`\n\n"
        "📋 *Olamlar ro'yxati:*\n`/listworlds`",
        parse_mode="Markdown"
    )

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

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(ChatJoinRequestHandler(approve_join))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_help))
app.add_handler(CommandHandler("listworlds", list_worlds))
app.add_handler(CommandHandler("newworld", cmd_newworld))
app.add_handler(CommandHandler("addtoworld", cmd_addtoworld))
app.add_handler(CommandHandler("delfromworld", cmd_delfromworld))
app.add_handler(CommandHandler("delworld", cmd_delworld))
app.add_handler(CommandHandler("del", cmd_del))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.VIDEO, save))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling(drop_pending_updates=True)
        

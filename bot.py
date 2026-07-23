"""
Buxgalteriya Telegram Bot
- Obunachilarga habar tarqatish
- Soliq sanalari eslatmasi
- /start - botga obuna bo'lish
- /habar <matn> - barcha obunachilarga habar yuborish (faqat admin)
- /soliq - soliq sanalari
- /obunalar - obunchilar soni (faqat admin)
"""

import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# ===== SOZLAMALAR =====
TOKEN = "8670321404:AAFE8UA_57nDmeLMq_DZ_Hlq8Gk_bsk9mpA"
ADMIN_ID = None  # Birinchi /start bosgan admin bo'ladi
USERS_FILE = "users.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ===== FOYDALANUVCHILARNI SAQLASH =====
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {"admin_id": None, "users": {}}

def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== SOLIQ SANALARI =====
SOLIQ_SANALARI = [
    {"oy": 1,  "kun": 25, "nomi": "QQS hisoboti (IV chorak)"},
    {"oy": 2,  "kun": 15, "nomi": "Foyda solig'i (yillik)"},
    {"oy": 2,  "kun": 25, "nomi": "QQS hisoboti (yanvar)"},
    {"oy": 3,  "kun": 25, "nomi": "QQS hisoboti (fevral)"},
    {"oy": 4,  "kun": 15, "nomi": "I chorak soliq hisoboti"},
    {"oy": 4,  "kun": 25, "nomi": "QQS hisoboti (mart)"},
    {"oy": 5,  "kun": 25, "nomi": "QQS hisoboti (aprel)"},
    {"oy": 6,  "kun": 25, "nomi": "QQS hisoboti (may)"},
    {"oy": 7,  "kun": 15, "nomi": "II chorak soliq hisoboti"},
    {"oy": 7,  "kun": 25, "nomi": "QQS hisoboti (iyun)"},
    {"oy": 8,  "kun": 25, "nomi": "QQS hisoboti (iyul)"},
    {"oy": 9,  "kun": 25, "nomi": "QQS hisoboti (avgust)"},
    {"oy": 10, "kun": 15, "nomi": "III chorak soliq hisoboti"},
    {"oy": 10, "kun": 25, "nomi": "QQS hisoboti (sentabr)"},
    {"oy": 11, "kun": 25, "nomi": "QQS hisoboti (oktabr)"},
    {"oy": 12, "kun": 25, "nomi": "QQS hisoboti (noyabr)"},
]

def get_upcoming_taxes(days=30):
    today = datetime.now()
    upcoming = []
    for s in SOLIQ_SANALARI:
        try:
            deadline = datetime(today.year, s["oy"], s["kun"])
            if deadline < today:
                deadline = datetime(today.year + 1, s["oy"], s["kun"])
            delta = (deadline - today).days
            if 0 <= delta <= days:
                upcoming.append({
                    "nomi": s["nomi"],
                    "sana": deadline.strftime("%d.%m.%Y"),
                    "qoldi": delta
                })
        except:
            pass
    return sorted(upcoming, key=lambda x: x["qoldi"])

# ===== BUYRUQLAR =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_users()

    # Birinchi foydalanuvchi admin bo'ladi
    if data["admin_id"] is None:
        data["admin_id"] = user.id
        save_users(data)

    # Foydalanuvchini ro'yxatga olish
    if str(user.id) not in data["users"]:
        data["users"][str(user.id)] = {
            "id": user.id,
            "ism": user.full_name,
            "username": user.username or "",
            "qoshildi": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        save_users(data)

        # Adminga xabar
        if data["admin_id"] and data["admin_id"] != user.id:
            try:
                await context.bot.send_message(
                    chat_id=data["admin_id"],
                    text=f"🆕 Yangi obunachi: {user.full_name} (@{user.username or 'username yoq'})"
                )
            except:
                pass

    keyboard = [["📅 Soliq sanalari", "ℹ️ Ma'lumot"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        f"🤖 Bu buxgalteriya yordamchi boti.\n\n"
        f"📅 /soliq — Yaqinlashayotgan soliq sanalari\n"
        f"ℹ️ /help — Yordam\n\n"
        f"✅ Siz muvaffaqiyatli obuna bo'ldingiz!",
        reply_markup=reply_markup
    )

async def soliq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upcoming = get_upcoming_taxes(60)

    if not upcoming:
        await update.message.reply_text("✅ Yaqin 60 kunda muhim soliq sanalari yo'q.")
        return

    matn = "📅 *Yaqinlashayotgan soliq sanalari:*\n\n"
    for s in upcoming:
        if s["qoldi"] == 0:
            emoji = "🔴"
            kun_text = "BUGUN!"
        elif s["qoldi"] <= 3:
            emoji = "🔴"
            kun_text = f"{s['qoldi']} kun qoldi"
        elif s["qoldi"] <= 7:
            emoji = "🟡"
            kun_text = f"{s['qoldi']} kun qoldi"
        else:
            emoji = "🟢"
            kun_text = f"{s['qoldi']} kun qoldi"

        matn += f"{emoji} *{s['nomi']}*\n"
        matn += f"   📆 {s['sana']} — {kun_text}\n\n"

    await update.message.reply_text(matn, parse_mode='Markdown')

async def habar_yuborish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin barcha obunachilarga habar yuboradi: /habar <matn>"""
    data = load_users()
    user_id = update.effective_user.id

    if data["admin_id"] != user_id:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun.")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 Ishlatish:\n/habar <matn>\n\n"
            "Misol:\n/habar Bugun QQS hisoboti topshirish oxirgi kun!"
        )
        return

    matn = ' '.join(context.args)
    users = data["users"]

    if not users:
        await update.message.reply_text("❌ Hali obunachi yo'q.")
        return

    yuborildi = 0
    xato = 0

    await update.message.reply_text(f"📤 {len(users)} ta obunachiga yuborilmoqda...")

    for uid, uinfo in users.items():
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 *E'lon*\n\n{matn}",
                parse_mode='Markdown'
            )
            yuborildi += 1
        except Exception as e:
            xato += 1
            logging.warning(f"Yuborib bo'lmadi {uid}: {e}")

    await update.message.reply_text(
        f"✅ Natija:\n"
        f"   Yuborildi: {yuborildi} ta\n"
        f"   Xato: {xato} ta"
    )

async def obunalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_users()
    if data["admin_id"] != update.effective_user.id:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun.")
        return

    users = data["users"]
    matn = f"👥 *Obunchilar: {len(users)} ta*\n\n"
    for uid, u in list(users.items())[-10:]:
        matn += f"• {u['ism']} (@{u['username'] or '—'}) — {u['qoshildi']}\n"

    await update.message.reply_text(matn, parse_mode='Markdown')

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_users()
    if data["admin_id"] != update.effective_user.id:
        await update.message.reply_text("❌ Siz admin emassiz.")
        return

    matn = (
        "⚙️ *Admin panel*\n\n"
        "/habar <matn> — Barcha obunachilarga habar yuborish\n"
        "/obunalar — Obunchilar ro'yxati\n"
        "/soliq — Soliq sanalari\n\n"
        "Misol:\n"
        "`/habar Bugun QQS hisoboti topshirish oxirgi kun!`"
    )
    await update.message.reply_text(matn, parse_mode='Markdown')

async def tugma_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matn = update.message.text
    if matn == "📅 Soliq sanalari":
        await soliq(update, context)
    elif matn == "ℹ️ Ma'lumot":
        await update.message.reply_text(
            "🤖 *Buxgalteriya yordamchi bot*\n\n"
            "📅 Soliq sanalarini kuzatib boradi\n"
            "📢 E'lonlarni tarqatadi\n\n"
            "Buyruqlar:\n"
            "/start — Botni boshlash\n"
            "/soliq — Yaqin soliq sanalari",
            parse_mode='Markdown'
        )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Yordam*\n\n"
        "/start — Botni boshlash / obuna bo'lish\n"
        "/soliq — Yaqinlashayotgan soliq sanalari\n\n"
        "Admin uchun:\n"
        "/habar <matn> — Hammaga habar yuborish\n"
        "/obunalar — Obunchilar soni\n"
        "/admin — Admin panel",
        parse_mode='Markdown'
    )

# ===== ASOSIY =====
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("soliq", soliq))
    app.add_handler(CommandHandler("habar", habar_yuborish))
    app.add_handler(CommandHandler("obunalar", obunalar))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tugma_handler))

    print("✅ Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

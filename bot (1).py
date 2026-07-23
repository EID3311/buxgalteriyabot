import logging
import json
import os
import asyncio
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8670321404:AAFE8UA_57nDmeLMq_DZ_Hlq8Gk_bsk9mpA"
USERS_FILE = "users.json"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"admin_id": None, "users": {}}

def save_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

SOLIQ_SANALARI = [
    (1, 25, "QQS hisoboti (IV chorak)"),
    (2, 15, "Foyda solig'i yillik"),
    (2, 25, "QQS hisoboti (yanvar)"),
    (3, 25, "QQS hisoboti (fevral)"),
    (4, 15, "I chorak soliq hisoboti"),
    (4, 25, "QQS hisoboti (mart)"),
    (5, 25, "QQS hisoboti (aprel)"),
    (6, 25, "QQS hisoboti (may)"),
    (7, 15, "II chorak soliq hisoboti"),
    (7, 25, "QQS hisoboti (iyun)"),
    (8, 25, "QQS hisoboti (iyul)"),
    (9, 25, "QQS hisoboti (avgust)"),
    (10, 15, "III chorak soliq hisoboti"),
    (10, 25, "QQS hisoboti (sentabr)"),
    (11, 25, "QQS hisoboti (oktabr)"),
    (12, 25, "QQS hisoboti (noyabr)"),
]

def get_upcoming_taxes():
    today = datetime.now()
    result = []
    for oy, kun, nom in SOLIQ_SANALARI:
        try:
            d = datetime(today.year, oy, kun)
            if d < today:
                d = datetime(today.year + 1, oy, kun)
            delta = (d - today).days
            if 0 <= delta <= 60:
                result.append((nom, d.strftime("%d.%m.%Y"), delta))
        except:
            pass
    return sorted(result, key=lambda x: x[2])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_users()
    if data["admin_id"] is None:
        data["admin_id"] = user.id
    if str(user.id) not in data["users"]:
        data["users"][str(user.id)] = {
            "id": user.id,
            "ism": user.full_name,
            "username": user.username or "",
            "qoshildi": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        save_users(data)
        if data["admin_id"] and data["admin_id"] != user.id:
            try:
                await context.bot.send_message(
                    chat_id=data["admin_id"],
                    text=f"🆕 Yangi obunachi: {user.full_name} (@{user.username or '-'})"
                )
            except:
                pass
    else:
        save_users(data)

    keyboard = ReplyKeyboardMarkup([["📅 Soliq sanalari", "ℹ️ Ma'lumot"]], resize_keyboard=True)
    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        "🤖 Buxgalteriya yordamchi botiga xush kelibsiz!\n\n"
        "📅 /soliq — Yaqin soliq sanalari\n"
        "📢 /habar <matn> — Hammaga xabar (admin)\n"
        "👥 /obunalar — Obunchilar soni (admin)\n\n"
        "✅ Obuna bo'ldingiz!",
        reply_markup=keyboard
    )

async def soliq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upcoming = get_upcoming_taxes()
    if not upcoming:
        await update.message.reply_text("✅ Yaqin 60 kunda muhim soliq sanalari yo'q.")
        return
    matn = "📅 *Yaqinlashayotgan soliq sanalari:*\n\n"
    for nom, sana, qoldi in upcoming:
        if qoldi <= 3:
            emoji = "🔴"
        elif qoldi <= 7:
            emoji = "🟡"
        else:
            emoji = "🟢"
        kun_text = "BUGUN!" if qoldi == 0 else f"{qoldi} kun qoldi"
        matn += f"{emoji} *{nom}*\n   📆 {sana} — {kun_text}\n\n"
    await update.message.reply_text(matn, parse_mode='Markdown')

async def habar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_users()
    if data["admin_id"] != update.effective_user.id:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun.")
        return
    if not context.args:
        await update.message.reply_text("📝 Ishlatish:\n/habar <matn>\n\nMisol:\n/habar Bugun QQS topshirish oxirgi kun!")
        return
    matn = ' '.join(context.args)
    users = data["users"]
    if not users:
        await update.message.reply_text("❌ Hali obunachi yo'q.")
        return
    yuborildi = 0
    xato = 0
    await update.message.reply_text(f"📤 {len(users)} ta obunachiga yuborilmoqda...")
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *E'lon*\n\n{matn}", parse_mode='Markdown')
            yuborildi += 1
        except:
            xato += 1
    await update.message.reply_text(f"✅ Yuborildi: {yuborildi} ta\n❌ Xato: {xato} ta")

async def obunalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_users()
    if data["admin_id"] != update.effective_user.id:
        await update.message.reply_text("❌ Faqat admin uchun.")
        return
    users = data["users"]
    matn = f"👥 *Jami obunchilar: {len(users)} ta*\n\n"
    for uid, u in list(users.items())[-10:]:
        matn += f"• {u['ism']} — {u['qoshildi']}\n"
    await update.message.reply_text(matn, parse_mode='Markdown')

async def tugma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📅 Soliq sanalari":
        await soliq(update, context)
    elif update.message.text == "ℹ️ Ma'lumot":
        await update.message.reply_text(
            "🤖 *Buxgalteriya yordamchi bot*\n\n"
            "📅 Soliq sanalarini kuzatadi\n"
            "📢 E'lonlarni tarqatadi\n\n"
            "/soliq — Yaqin soliq sanalari\n"
            "/start — Qayta boshlash",
            parse_mode='Markdown'
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("soliq", soliq))
    app.add_handler(CommandHandler("habar", habar))
    app.add_handler(CommandHandler("obunalar", obunalar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tugma))
    print("✅ Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()

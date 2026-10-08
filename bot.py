import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
DB_PATH = "members.db"

logging.basicConfig(level=logging.INFO)

def conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS members (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        status TEXT DEFAULT 'unknown',
        active INTEGER DEFAULT 1
    )""")
    c.commit()
    return c

def save_user(u):
    c = conn()
    c.execute("""INSERT INTO members(user_id,username,first_name)
                 VALUES(?,?,?)
                 ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username, first_name=excluded.first_name,
                 active=1""",
              (u.id, u.username or "", u.first_name or ""))
    c.commit(); c.close()

def set_status(uid, status):
    c = conn()
    c.execute("UPDATE members SET status=?,active=1 WHERE user_id=?", (status, uid))
    c.commit(); c.close()

def users(status=None):
    c = conn()
    q = "SELECT user_id FROM members WHERE active=1"
    args = ()
    if status:
        q += " AND status=?"; args = (status,)
    rows = c.execute(q, args).fetchall()
    c.close()
    return [r[0] for r in rows]

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ I'm Interested", callback_data="interested")],
        [InlineKeyboardButton("❌ Not Interested", callback_data="not_interested")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    await update.message.reply_text(
        "Hi ❤️\n\nThis is Shruti’s Meet & Channel Assistant.\n\n"
        "If you’re genuinely interested in meeting, please choose an option below. 😊",
        reply_markup=menu())

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    await update.message.reply_text("Please choose your current interest:", reply_markup=menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to register or /status to update your response.")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    save_user(q.from_user)
    if q.data == "interested":
        set_status(q.from_user.id, "interested")
        await q.edit_message_text("❤️ Thanks! I’ve marked you as interested.")
    else:
        set_status(q.from_user.id, "not_interested")
        await q.edit_message_text("No problem 😊 Your response has been updated.")

def admin_only(u): return u.id == ADMIN_ID

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update.effective_user):
        return await update.message.reply_text("Admin only.")
    c = conn()
    total = c.execute("SELECT COUNT(*) FROM members WHERE active=1").fetchone()[0]
    interested = c.execute("SELECT COUNT(*) FROM members WHERE active=1 AND status='interested'").fetchone()[0]
    c.close()
    await update.message.reply_text(f"📊 Registered: {total}\n❤️ Interested: {interested}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update.effective_user):
        return await update.message.reply_text("Admin only.")
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        return await update.message.reply_text("Use: /broadcast Your message")
    sent = failed = 0
    for uid in users():
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"📢 Sent: {sent}\nFailed: {failed}")

async def interested(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update.effective_user):
        return await update.message.reply_text("Admin only.")
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        return await update.message.reply_text("Use: /interested Your message")
    sent = failed = 0
    for uid in users("interested"):
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"❤️ Sent: {sent}\nFailed: {failed}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("interested", interested))
app.add_handler(CallbackQueryHandler(buttons))
app.run_polling()

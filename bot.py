import os, sqlite3, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN=os.environ["BOT_TOKEN"]
ADMIN_ID=int(os.environ["ADMIN_ID"])
DB="members.db"
logging.basicConfig(level=logging.INFO)

def db():
    c=sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS members(
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, status TEXT DEFAULT 'unknown',
        active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.commit(); return c

def save(u):
    c=db()
    c.execute("""INSERT INTO members(user_id,username,first_name,last_name)
        VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username, first_name=excluded.first_name,
        last_name=excluded.last_name, active=1, updated_at=CURRENT_TIMESTAMP""",
        (u.id,u.username or "",u.first_name or "",u.last_name or ""))
    c.commit(); c.close()

def status(uid,s):
    c=db(); c.execute("UPDATE members SET status=?,active=1,updated_at=CURRENT_TIMESTAMP WHERE user_id=?",(s,uid)); c.commit(); c.close()

def users(s=None):
    c=db()
    q="SELECT user_id FROM members WHERE active=1"
    a=()
    if s: q+=" AND status=?"; a=(s,)
    r=c.execute(q,a).fetchall(); c.close(); return [x[0] for x in r]

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ I'm Interested",callback_data="yes")],
        [InlineKeyboardButton("❌ Not Interested",callback_data="no")],
        [InlineKeyboardButton("🔄 Change Status",callback_data="change")]])

async def start(u,ctx):
    save(u.effective_user)
    await u.message.reply_text(
        "🌸 Welcome!\n\nThis is Shruti’s Meet & Channel Assistant.\n\n"
        "If you’re genuinely interested in meeting, please choose your current status. ❤️",
        reply_markup=menu())

async def status_cmd(u,ctx):
    save(u.effective_user)
    await u.message.reply_text("Please choose your current status:",reply_markup=menu())

async def help_cmd(u,ctx):
    await u.message.reply_text("Use /start or /status to update your interest.")

async def buttons(u,ctx):
    q=u.callback_query; await q.answer(); save(q.from_user)
    if q.data=="yes":
        status(q.from_user.id,"interested")
        await q.edit_message_text("❤️ Thanks! You’re marked as interested.")
    elif q.data=="no":
        status(q.from_user.id,"not_interested")
        await q.edit_message_text("No problem 😊 Your status has been updated.")
    else:
        await q.edit_message_text("Please choose your current status:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❤️ I'm Interested",callback_data="yes")],
                [InlineKeyboardButton("❌ Not Interested",callback_data="no")]]))

def admin(u): return u.effective_user.id==ADMIN_ID

async def stats(u,ctx):
    if not admin(u): return await u.message.reply_text("Admin only.")
    c=db(); r=c.execute("""SELECT COUNT(*),
      SUM(status='interested'),SUM(status='not_interested'),SUM(status='unknown')
      FROM members WHERE active=1""").fetchone(); c.close()
    await u.message.reply_text(f"📊 Stats\n\n👥 Registered: {r[0] or 0}\n❤️ Interested: {r[1] or 0}\n❌ Not Interested: {r[2] or 0}\n❔ No status: {r[3] or 0}")

async def members(u,ctx):
    if not admin(u): return await u.message.reply_text("Admin only.")
    c=db(); rows=c.execute("SELECT user_id,first_name,last_name,username,status FROM members WHERE active=1 ORDER BY updated_at DESC LIMIT 50").fetchall(); c.close()
    if not rows: return await u.message.reply_text("No members yet.")
    out=["👥 Members\n"]
    for i,(uid,fn,ln,un,st) in enumerate(rows,1):
        name=" ".join(x for x in (fn,ln) if x) or "Unknown"
        out.append(f"{i}. {'❤️' if st=='interested' else '❌' if st=='not_interested' else '❔'} {name} — @{un if un else 'no_username'} — {uid}")
    await u.message.reply_text("\n".join(out)[:4000])

async def member(u,ctx):
    if not admin(u): return await u.message.reply_text("Admin only.")
    if not ctx.args or not ctx.args[0].isdigit(): return await u.message.reply_text("Use: /member 123456789")
    c=db(); r=c.execute("SELECT user_id,first_name,last_name,username,status,active,created_at,updated_at FROM members WHERE user_id=?",(int(ctx.args[0]),)).fetchone(); c.close()
    if not r: return await u.message.reply_text("Member not found.")
    uid,fn,ln,un,st,act,cr,up=r
    await u.message.reply_text(f"👤 Member\n\nName: {' '.join(x for x in (fn,ln) if x) or 'Unknown'}\nUsername: @{un if un else 'none'}\nID: {uid}\nStatus: {st}\nActive: {'Yes' if act else 'No'}\nRegistered: {cr}\nUpdated: {up}")

async def broadcast(u,ctx):
    if not admin(u): return await u.message.reply_text("Admin only.")
    text=u.message.text.partition(" ")[2].strip()
    if not text: return await u.message.reply_text("Use: /broadcast Your message")
    sent=failed=0
    for uid in users():
        try: await ctx.bot.send_message(uid,text); sent+=1
        except Exception: failed+=1
    await u.message.reply_text(f"📢 Sent: {sent}\nFailed: {failed}")

async def interested(u,ctx):
    if not admin(u): return await u.message.reply_text("Admin only.")
    text=u.message.text.partition(" ")[2].strip()
    if not text: return await u.message.reply_text("Use: /interested Your message")
    sent=failed=0
    for uid in users("interested"):
        try: await ctx.bot.send_message(uid,text); sent+=1
        except Exception: failed+=1
    await u.message.reply_text(f"❤️ Sent: {sent}\nFailed: {failed}")

app=Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("status",status_cmd))
app.add_handler(CommandHandler("help",help_cmd))
app.add_handler(CommandHandler("admin",stats))
app.add_handler(CommandHandler("members",members))
app.add_handler(CommandHandler("member",member))
app.add_handler(CommandHandler("broadcast",broadcast))
app.add_handler(CommandHandler("interested",interested))
app.add_handler(CallbackQueryHandler(buttons))
app.run_polling()

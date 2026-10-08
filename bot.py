import os
import sqlite3
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

# Add this in Railway Variables:
# CHANNEL_ID=-1003777733349
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

DB = "members.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# =========================================================
# DATABASE
# =========================================================

def db():
    c = sqlite3.connect(DB)

    c.execute("""
        CREATE TABLE IF NOT EXISTS members(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            status TEXT DEFAULT 'unknown',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.commit()
    return c


def save(u):
    c = db()

    c.execute("""
        INSERT INTO members(
            user_id,
            username,
            first_name,
            last_name
        )
        VALUES(?,?,?,?)

        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            active=1,
            updated_at=CURRENT_TIMESTAMP
    """, (
        u.id,
        u.username or "",
        u.first_name or "",
        u.last_name or ""
    ))

    c.commit()
    c.close()


def status(uid, s):
    c = db()

    c.execute(
        """
        UPDATE members
        SET status=?,
            active=1,
            updated_at=CURRENT_TIMESTAMP
        WHERE user_id=?
        """,
        (s, uid)
    )

    c.commit()
    c.close()


def users(s=None):
    c = db()

    q = "SELECT user_id FROM members WHERE active=1"
    a = ()

    if s:
        q += " AND status=?"
        a = (s,)

    r = c.execute(q, a).fetchall()

    c.close()

    return [x[0] for x in r]


# =========================================================
# MAIN MENU
# =========================================================

def menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💰 Meet later — financial reasons",
                callback_data="financial"
            )
        ],
        [
            InlineKeyboardButton(
                "📍 Meet later — currently outside Bangalore",
                callback_data="outside_bangalore"
            )
        ],
        [
            InlineKeyboardButton(
                "✈️ Interested in meeting outside Bangalore",
                callback_data="outside_city"
            )
        ],
        [
            InlineKeyboardButton(
                "❤️ I’m ready to confirm the meet",
                callback_data="ready"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ I’m not interested anymore",
                callback_data="not_interested"
            )
        ],
    ])


# =========================================================
# CONFIRMATION MENU
# =========================================================

def confirm_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❤️ Ready to confirm with ₹1K advance & stay in channel",
                callback_data="ready"
            )
        ],
        [
            InlineKeyboardButton(
                "⏳ Not ready — remove me from channel",
                callback_data="remove"
            )
        ],
    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save(update.effective_user)

    await update.message.reply_text(
        "🌸 Welcome!\n\n"
        "This is Shruti’s Meet & Channel Assistant.\n\n"
        "If you’re genuinely interested in meeting, "
        "please choose your current status. ❤️",
        reply_markup=menu()
    )


# =========================================================
# STATUS COMMAND
# =========================================================

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save(update.effective_user)

    await update.message.reply_text(
        "Please choose your current status:",
        reply_markup=menu()
    )


# =========================================================
# HELP
# =========================================================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use /start or /status to update your interest."
    )


# =========================================================
# REMOVE USER FROM CHANNEL
# =========================================================

async def remove_from_channel(bot, user_id):
    if not CHANNEL_ID:
        logging.warning("CHANNEL_ID is not configured.")
        return False

    try:
        await bot.ban_chat_member(
            chat_id=int(CHANNEL_ID),
            user_id=user_id
        )

        logging.info(
            "Removed user %s from channel",
            user_id
        )

        return True

    except Exception:
        logging.exception(
            "Could not remove user %s from channel",
            user_id
        )

        return False


# =========================================================
# FINANCIAL REASONS MESSAGE
# =========================================================

async def send_financial(query):

    text = """
Okay, I understand that. ❤️

Shruti would like to keep her private channel for people who are genuinely interested in meeting her or who have already met her.

I hope you’ve seen and acknowledged this channel update:
<a href="https://t.me/c/3777733349/230">Channel update</a>

So, if you’d like to continue staying in the channel, a ₹1K advance is required for confirmation now. The remaining amount can be paid during the meet. 😊

If you’re not ready to confirm with the ₹1K advance now, you can choose the option below to leave the channel.
"""

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=confirm_menu()
    )


# =========================================================
# OUTSIDE BANGALORE MESSAGE
# =========================================================

async def send_outside_bangalore(query):

    text = """
Okay, I understand. ❤️

Since you’re currently outside Bangalore, no worries. Shruti would like to keep her private channel for people who are genuinely interested in meeting her or who have already met her.

I hope you’ve seen and acknowledged this channel update:
<a href="https://t.me/c/3777733349/230">Channel update</a>

So, if you’d like to continue staying in the channel, a ₹1K advance is required for confirmation now. The remaining amount can be paid during the meet. 😊

If you’re not ready to confirm with the ₹1K advance now, you can choose the option below to leave the channel.
"""

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=confirm_menu()
    )


# =========================================================
# OUTSIDE CITY MESSAGE
# =========================================================

async def send_outside_city(query):

    text = """
That’s nice to hear. ❤️

Since you’re interested in meeting outside Bangalore, Shruti would like to keep her private channel for people who are genuinely serious about meeting her or who have already met her.

I hope you’ve seen and acknowledged this channel update:
<a href="https://t.me/c/3777733349/230">Channel update</a>

If you’d like to continue staying in the channel, a ₹1K advance is required for confirmation now. The remaining amount can be paid during the meet. 😊

If you’re not ready to confirm with the ₹1K advance now, you can choose the option below to leave the channel.

✈️ For out-of-city meets:

For the terms, conditions, travel arrangements, and other details, please contact my Miss Boss @shruti23official directly. ❤️ She’ll guide you through everything. 😊
"""

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=confirm_menu()
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    save(query.from_user)

    # -----------------------------------------------------
    # FINANCIAL REASONS
    # -----------------------------------------------------

    if query.data == "financial":

        status(
            query.from_user.id,
            "meet_later_financial"
        )

        await send_financial(query)

    # -----------------------------------------------------
    # CURRENTLY OUTSIDE BANGALORE
    # -----------------------------------------------------

    elif query.data == "outside_bangalore":

        status(
            query.from_user.id,
            "meet_later_outside_bangalore"
        )

        await send_outside_bangalore(query)

    # -----------------------------------------------------
    # INTERESTED OUTSIDE BANGALORE
    # -----------------------------------------------------

    elif query.data == "outside_city":

        status(
            query.from_user.id,
            "interested_outside_city"
        )

        await send_outside_city(query)

    # -----------------------------------------------------
    # READY TO CONFIRM
    # -----------------------------------------------------

    elif query.data == "ready":

        status(
            query.from_user.id,
            "ready_to_confirm"
        )

        await query.edit_message_text(
            "❤️ Perfect! I’m glad you’re ready to confirm. 😊\n\n"
            "Please contact my Miss Boss @shruti23official "
            "to confirm the meet with the ₹1K advance.\n\n"
            "Once the advance is confirmed, she’ll guide you "
            "through the next steps. ❤️",

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💬 Contact @shruti23official",
                        url="https://t.me/shruti23official"
                    )
                ]
            ])
        )

    # -----------------------------------------------------
    # REMOVE — NOT READY
    # -----------------------------------------------------

    elif query.data == "remove":

        status(
            query.from_user.id,
            "removed"
        )

        await remove_from_channel(
            context.bot,
            query.from_user.id
        )

        await query.edit_message_text(
            "No problem 😊\n\n"
            "You’ve been removed from the channel.\n\n"
            "If you’d like to join again later, "
            "please contact Miss Boss @shruti23official. ❤️"
        )

    # -----------------------------------------------------
    # NOT INTERESTED
    # -----------------------------------------------------

    elif query.data == "not_interested":

        status(
            query.from_user.id,
            "not_interested"
        )

        await remove_from_channel(
            context.bot,
            query.from_user.id
        )

        await query.edit_message_text(
            "No problem 😊\n\n"
            "You’ve been removed from the channel.\n\n"
            "If you’d like to join again later, "
            "please contact Miss Boss @shruti23official. ❤️"
        )


# =========================================================
# ADMIN CHECK
# =========================================================

def admin(update: Update):
    return update.effective_user.id == ADMIN_ID


# =========================================================
# ADMIN STATS
# =========================================================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    c = db()

    r = c.execute("""
        SELECT
            COUNT(*),
            SUM(status='interested'),
            SUM(status='not_interested'),
            SUM(status='unknown')
        FROM members
        WHERE active=1
    """).fetchone()

    c.close()

    await update.message.reply_text(
        f"📊 Stats\n\n"
        f"👥 Registered: {r[0] or 0}\n"
        f"❤️ Interested: {r[1] or 0}\n"
        f"❌ Not Interested: {r[2] or 0}\n"
        f"❔ No status: {r[3] or 0}"
    )


# =========================================================
# MEMBERS
# =========================================================

async def members(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    c = db()

    rows = c.execute("""
        SELECT
            user_id,
            first_name,
            last_name,
            username,
            status
        FROM members
        WHERE active=1
        ORDER BY updated_at DESC
        LIMIT 50
    """).fetchall()

    c.close()

    if not rows:
        return await update.message.reply_text(
            "No members yet."
        )

    out = ["👥 Members\n"]

    for i, (uid, fn, ln, un, st) in enumerate(rows, 1):

        name = " ".join(
            x for x in (fn, ln)
            if x
        ) or "Unknown"

        if st == "interested":
            icon = "❤️"
        elif st == "not_interested":
            icon = "❌"
        else:
            icon = "❔"

        out.append(
            f"{i}. {icon} {name} — "
            f"@{un if un else 'no_username'} — {uid}"
        )

    await update.message.reply_text(
        "\n".join(out)[:4000]
    )


# =========================================================
# SINGLE MEMBER
# =========================================================

async def member(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    if (
        not context.args
        or not context.args[0].isdigit()
    ):
        return await update.message.reply_text(
            "Use: /member 123456789"
        )

    c = db()

    r = c.execute("""
        SELECT
            user_id,
            first_name,
            last_name,
            username,
            status,
            active,
            created_at,
            updated_at
        FROM members
        WHERE user_id=?
    """, (
        int(context.args[0]),
    )).fetchone()

    c.close()

    if not r:
        return await update.message.reply_text(
            "Member not found."
        )

    (
        uid,
        fn,
        ln,
        un,
        st,
        act,
        cr,
        up
    ) = r

    name = " ".join(
        x for x in (fn, ln)
        if x
    ) or "Unknown"

    await update.message.reply_text(
        f"👤 Member\n\n"
        f"Name: {name}\n"
        f"Username: @{un if un else 'none'}\n"
        f"ID: {uid}\n"
        f"Status: {st}\n"
        f"Active: {'Yes' if act else 'No'}\n"
        f"Registered: {cr}\n"
        f"Updated: {up}"
    )


# =========================================================
# BROADCAST
# =========================================================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    text = update.message.text.partition(" ")[2].strip()

    if not text:
        return await update.message.reply_text(
            "Use: /broadcast Your message"
        )

    sent = 0
    failed = 0

    for uid in users():

        try:
            await context.bot.send_message(
                uid,
                text
            )

            sent += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 Sent: {sent}\n"
        f"Failed: {failed}"
    )


# =========================================================
# INTERESTED BROADCAST
# =========================================================

async def interested(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    text = update.message.text.partition(" ")[2].strip()

    if not text:
        return await update.message.reply_text(
            "Use: /interested Your message"
        )

    sent = 0
    failed = 0

    for uid in users("interested"):

        try:
            await context.bot.send_message(
                uid,
                text
            )

            sent += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        f"❤️ Sent: {sent}\n"
        f"Failed: {failed}"
    )


# =========================================================
# START BOT
# =========================================================

app = (
    Application
    .builder()
    .token(TOKEN)
    .build()
)


app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("status", status_cmd)
)

app.add_handler(
    CommandHandler("help", help_cmd)
)

app.add_handler(
    CommandHandler("admin", stats)
)

app.add_handler(
    CommandHandler("members", members)
)

app.add_handler(
    CommandHandler("member", member)
)

app.add_handler(
    CommandHandler("broadcast", broadcast)
)

app.add_handler(
    CommandHandler("interested", interested)
)

app.add_handler(
    CallbackQueryHandler(buttons)
)


# =========================================================
# RUN
# =========================================================

app.run_polling()

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
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()

DB = "members.db"


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# DATABASE
# =========================================================

def db():
    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
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

    conn.commit()
    return conn


def save_user(user):
    conn = db()

    conn.execute("""
        INSERT INTO members (
            user_id,
            username,
            first_name,
            last_name
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            active = 1,
            updated_at = CURRENT_TIMESTAMP
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
        user.last_name or "",
    ))

    conn.commit()
    conn.close()


def set_status(user_id, status):
    conn = db()

    conn.execute("""
        UPDATE members
        SET status = ?,
            active = 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (status, user_id))

    conn.commit()
    conn.close()


def set_removed(user_id):
    conn = db()

    conn.execute("""
        UPDATE members
        SET status = 'removed',
            active = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def get_users(status=None):
    conn = db()

    if status:
        rows = conn.execute("""
            SELECT user_id
            FROM members
            WHERE active = 1
            AND status = ?
        """, (status,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT user_id
            FROM members
            WHERE active = 1
        """).fetchall()

    conn.close()

    return [row[0] for row in rows]


# =========================================================
# FIRST MENU
# =========================================================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❤️ I’m Interested",
                callback_data="interested"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ I’m Not Interested",
                callback_data="not_interested"
            )
        ],
    ])


# =========================================================
# INTERESTED MENU
# =========================================================

def interested_menu():
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
                "❤️ I’m ready to confirm the meet now",
                callback_data="ready"
            )
        ],
    ])


# =========================================================
# CONFIRMATION MENU
# =========================================================

def confirmation_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❤️ Ready to confirm & stay in channel",
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

    save_user(update.effective_user)

    await update.message.reply_text(
        "😎 Heyyy! I’m Miss Bot! 🤖🌸\n\n"
        "I’m Miss Shruti’s little AI Assistant ❤️\n\n"
        "I’m here to help you navigate her private channel, "
        "understand the options, and guide you through the "
        "next steps. 😊\n\n"
        "Ready? Let’s get started! ✨👇",
        reply_markup=main_menu(),
    )


# =========================================================
# STATUS COMMAND
# =========================================================

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    await update.message.reply_text(
        "Please choose an option below. ❤️",
        reply_markup=main_menu(),
    )


# =========================================================
# HELP
# =========================================================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Use /start or /status to update your interest."
    )


# =========================================================
# REMOVE FROM CHANNEL
# =========================================================

async def remove_from_channel(bot, user_id):

    if not CHANNEL_ID:
        logger.error("CHANNEL_ID is missing.")
        return False, "CHANNEL_ID is not configured."

    try:
        chat_id = int(CHANNEL_ID)
    except ValueError:
        logger.error("Invalid CHANNEL_ID: %s", CHANNEL_ID)
        return False, "CHANNEL_ID is invalid."

    try:

        me = await bot.get_me()

        bot_member = await bot.get_chat_member(
            chat_id,
            me.id
        )

        can_restrict = getattr(
            bot_member,
            "can_restrict_members",
            False
        )

        if not can_restrict:
            return False, "Bot does not have permission to remove members."

        await bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )

        logger.info(
            "Removed user %s from channel %s",
            user_id,
            chat_id
        )

        # Unban immediately so the person is removed,
        # but not permanently banned.
        try:
            await bot.unban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                only_if_banned=True
            )
        except Exception:
            logger.exception("User removed but unban failed.")

        return True, None

    except Exception as error:

        logger.exception(
            "Failed to remove user %s",
            user_id
        )

        return False, str(error)


async def remove_and_reply(
    query,
    context,
    user_id
):

    success, error = await remove_from_channel(
        context.bot,
        user_id
    )

    if success:

        set_removed(user_id)

        await query.edit_message_text(
            "❌ No problem 😊\n\n"
            "You’ve been removed from the channel.\n\n"
            "If you’d like to join again later, please contact "
            "Miss Boss @shruti23official. ❤️"
        )

    else:

        logger.error(
            "Removal failed for %s: %s",
            user_id,
            error
        )

        await query.edit_message_text(
            "❌ No problem 😊\n\n"
            "I couldn’t remove you from the channel automatically.\n\n"
            "Please contact Miss Boss @shruti23official "
            "and she’ll remove you. ❤️"
        )


# =========================================================
# FINANCIAL OPTION
# =========================================================

async def financial_message(query):

    set_status(
        query.from_user.id,
        "meet_later_financial"
    )

    text = (
        "Okay, I understand that. ❤️\n\n"
        "Shruti would like to keep her private channel for people "
        "who are genuinely interested in meeting her or who have "
        "already met her.\n\n"
        "I hope you’ve seen and acknowledged this channel update:\n"
        '<a href="https://t.me/c/3777733349/230">Channel update</a>\n\n'
        "If you’d like to continue staying in the channel, "
        "confirmation is required now. 😊\n\n"
        "If you’re not ready to proceed now, you can choose "
        "the option below to leave the channel."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=confirmation_menu()
    )


# =========================================================
# OUTSIDE BANGALORE
# =========================================================

async def outside_bangalore_message(query):

    set_status(
        query.from_user.id,
        "meet_later_outside_bangalore"
    )

    text = (
        "Okay, I understand. ❤️\n\n"
        "Since you’re currently outside Bangalore, no worries. "
        "Shruti would like to keep her private channel for people "
        "who are genuinely interested in meeting her or who have "
        "already met her.\n\n"
        "I hope you’ve seen and acknowledged this channel update:\n"
        '<a href="https://t.me/c/3777733349/230">Channel update</a>\n\n'
        "If you’d like to continue staying in the channel, "
        "confirmation is required now. 😊\n\n"
        "If you’re not ready to proceed now, you can choose "
        "the option below to leave the channel."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=confirmation_menu()
    )


# =========================================================
# OUTSIDE CITY
# =========================================================

async def outside_city_message(query):

    set_status(
        query.from_user.id,
        "interested_outside_city"
    )

    text = (
        "That’s nice to hear. ❤️\n\n"
        "Since you’re interested in meeting outside Bangalore, "
        "Shruti would like to keep her private channel for people "
        "who are genuinely serious about meeting her or who have "
        "already met her.\n\n"
        "I hope you’ve seen and acknowledged this channel update:\n"
        '<a href="https://t.me/c/3777733349/230">Channel update</a>\n\n'
        "If you’d like to continue staying in the channel, "
        "confirmation is required now. 😊\n\n"
        "If you’re not ready to proceed now, you can choose "
        "the option below to leave the channel.\n\n"
        "✈️ For out-of-city arrangements and other details, "
        "please contact Miss Boss @shruti23official directly. ❤️"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=confirmation_menu()
    )


# =========================================================
# READY
# =========================================================

async def ready_message(query):

    set_status(
        query.from_user.id,
        "ready_to_confirm"
    )

    await query.edit_message_text(
        "❤️ Perfect! I’m glad you’re ready to proceed. 😊\n\n"
        "Please contact Miss Boss @shruti23official "
        "to discuss and confirm the next steps. ❤️",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💬 Contact @shruti23official",
                    url="https://t.me/shruti23official"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ I changed my mind",
                    callback_data="remove"
                )
            ],
        ])
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    save_user(query.from_user)

    user_id = query.from_user.id


    # -----------------------------------------------------
    # INTERESTED
    # -----------------------------------------------------

    if query.data == "interested":

        set_status(
            user_id,
            "interested"
        )

        await query.edit_message_text(
            "Aww, nice to know you’re interested! 🥰❤️\n\n"
            "Before we continue, please choose the option that "
            "best describes your current situation. "
            "This will help me guide you correctly. 😊",
            reply_markup=interested_menu()
        )


    # -----------------------------------------------------
    # NOT INTERESTED
    # -----------------------------------------------------

    elif query.data == "not_interested":

        set_status(
            user_id,
            "not_interested"
        )

        await remove_and_reply(
            query,
            context,
            user_id
        )


    # -----------------------------------------------------
    # FINANCIAL
    # -----------------------------------------------------

    elif query.data == "financial":

        await financial_message(query)


    # -----------------------------------------------------
    # OUTSIDE BANGALORE
    # -----------------------------------------------------

    elif query.data == "outside_bangalore":

        await outside_bangalore_message(query)


    # -----------------------------------------------------
    # OUTSIDE CITY
    # -----------------------------------------------------

    elif query.data == "outside_city":

        await outside_city_message(query)


    # -----------------------------------------------------
    # READY
    # -----------------------------------------------------

    elif query.data == "ready":

        await ready_message(query)


    # -----------------------------------------------------
    # REMOVE
    # -----------------------------------------------------

    elif query.data == "remove":

        await remove_and_reply(
            query,
            context,
            user_id
        )


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID


# =========================================================
# ADMIN STATS
# =========================================================

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    conn = db()

    result = conn.execute("""
        SELECT
            COUNT(*),
            SUM(status='interested'),
            SUM(status='not_interested'),
            SUM(status='meet_later_financial'),
            SUM(status='meet_later_outside_bangalore'),
            SUM(status='interested_outside_city'),
            SUM(status='ready_to_confirm'),
            SUM(status='removed')
        FROM members
    """).fetchone()

    conn.close()

    await update.message.reply_text(
        "📊 Bot Statistics\n\n"
        f"👥 Registered: {result[0] or 0}\n"
        f"❤️ Interested: {result[1] or 0}\n"
        f"❌ Not Interested: {result[2] or 0}\n"
        f"💰 Financial reasons: {result[3] or 0}\n"
        f"📍 Outside Bangalore: {result[4] or 0}\n"
        f"✈️ Outside-city interest: {result[5] or 0}\n"
        f"✅ Ready: {result[6] or 0}\n"
        f"🚫 Removed: {result[7] or 0}"
    )


# =========================================================
# ALL MEMBERS
# =========================================================

async def members(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    conn = db()

    rows = conn.execute("""
        SELECT
            user_id,
            first_name,
            last_name,
            username,
            status,
            active
        FROM members
        ORDER BY updated_at DESC
        LIMIT 100
    """).fetchall()

    conn.close()

    if not rows:
        return await update.message.reply_text(
            "No members yet."
        )

    status_names = {
        "interested":
            "❤️ Interested",

        "not_interested":
            "❌ Not Interested",

        "meet_later_financial":
            "💰 Meet later — financial reasons",

        "meet_later_outside_bangalore":
            "📍 Meet later — outside Bangalore",

        "interested_outside_city":
            "✈️ Interested outside Bangalore",

        "ready_to_confirm":
            "✅ Ready to confirm",

        "removed":
            "🚫 Removed",

        "unknown":
            "❔ Unknown",
    }

    output = ["👥 Members\n"]

    for i, row in enumerate(rows, 1):

        (
            user_id,
            first_name,
            last_name,
            username,
            status,
            active
        ) = row

        name = " ".join(
            x for x in (first_name, last_name)
            if x
        ) or "Unknown"

        status_text = status_names.get(
            status,
            status
        )

        output.append(
            f"{i}. {name}\n"
            f"   Username: @{username if username else 'none'}\n"
            f"   ID: {user_id}\n"
            f"   Status: {status_text}\n"
            f"   Active: {'Yes' if active else 'No'}\n"
        )

    message = "\n".join(output)

    for i in range(0, len(message), 4000):
        await update.message.reply_text(
            message[i:i + 4000]
        )


# =========================================================
# SINGLE MEMBER
# =========================================================

async def member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
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

    user_id = int(context.args[0])

    conn = db()

    row = conn.execute("""
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
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    conn.close()

    if not row:
        return await update.message.reply_text(
            "Member not found."
        )

    (
        uid,
        first_name,
        last_name,
        username,
        status,
        active,
        created,
        updated
    ) = row

    status_names = {
        "interested": "❤️ Interested",
        "not_interested": "❌ Not Interested",
        "meet_later_financial":
            "💰 Meet later — financial reasons",
        "meet_later_outside_bangalore":
            "📍 Meet later — outside Bangalore",
        "interested_outside_city":
            "✈️ Interested outside Bangalore",
        "ready_to_confirm":
            "✅ Ready to confirm",
        "removed":
            "🚫 Removed",
    }

    name = " ".join(
        x for x in (first_name, last_name)
        if x
    ) or "Unknown"

    await update.message.reply_text(
        "👤 Member\n\n"
        f"Name: {name}\n"
        f"Username: @{username if username else 'none'}\n"
        f"ID: {uid}\n"
        f"Status: {status_names.get(status, status)}\n"
        f"Active: {'Yes' if active else 'No'}\n"
        f"Registered: {created}\n"
        f"Updated: {updated}"
    )


# =========================================================
# INTERESTED LIST
# =========================================================

async def interested_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    conn = db()

    rows = conn.execute("""
        SELECT
            user_id,
            first_name,
            last_name,
            username,
            status
        FROM members
        WHERE status IN (
            'interested',
            'meet_later_financial',
            'meet_later_outside_bangalore',
            'interested_outside_city',
            'ready_to_confirm'
        )
        ORDER BY updated_at DESC
    """).fetchall()

    conn.close()

    if not rows:
        return await update.message.reply_text(
            "❤️ No interested members yet."
        )

    status_names = {
        "interested":
            "❤️ Interested",

        "meet_later_financial":
            "💰 Meet later — financial reasons",

        "meet_later_outside_bangalore":
            "📍 Meet later — currently outside Bangalore",

        "interested_outside_city":
            "✈️ Interested in meeting outside Bangalore",

        "ready_to_confirm":
            "✅ Ready to confirm",
    }

    output = ["❤️ Interested Members\n"]

    for i, row in enumerate(rows, 1):

        (
            user_id,
            first_name,
            last_name,
            username,
            status
        ) = row

        name = " ".join(
            x for x in (first_name, last_name)
            if x
        ) or "Unknown"

        output.append(
            f"{i}. {name}\n"
            f"   Username: @{username if username else 'none'}\n"
            f"   ID: {user_id}\n"
            f"   Status: {status_names.get(status, status)}\n"
        )

    message = "\n".join(output)

    for i in range(0, len(message), 4000):
        await update.message.reply_text(
            message[i:i + 4000]
        )


# =========================================================
# BROADCAST
# =========================================================

async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
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

    for user_id in get_users():

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text
            )
            sent += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 Sent: {sent}\n"
        f"Failed: {failed}"
    )


# =========================================================
# BROADCAST TO INTERESTED USERS
# =========================================================

async def interested_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return await update.message.reply_text(
            "Admin only."
        )

    text = update.message.text.partition(" ")[2].strip()

    if not text:
        return await update.message.reply_text(
            "Use: /interested Your message"
        )

    interested_statuses = [
        "interested",
        "meet_later_financial",
        "meet_later_outside_bangalore",
        "interested_outside_city",
        "ready_to_confirm",
    ]

    conn = db()

    placeholders = ",".join(
        "?" for _ in interested_statuses
    )

    rows = conn.execute(
        f"""
        SELECT user_id
        FROM members
        WHERE active = 1
        AND status IN ({placeholders})
        """,
        interested_statuses
    ).fetchall()

    conn.close()

    sent = 0
    failed = 0

    for row in rows:

        try:

            await context.bot.send_message(
                chat_id=row[0],
                text=text
            )

            sent += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        f"❤️ Sent: {sent}\n"
        f"Failed: {failed}"
    )


# =========================================================
# APPLICATION
# =========================================================

app = (
    Application
    .builder()
    .token(TOKEN)
    .build()
)


# Commands

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
    CommandHandler("interestedlist", interested_list)
)

app.add_handler(
    CommandHandler("broadcast", broadcast)
)

app.add_handler(
    CommandHandler("interested", interested_broadcast)
)


# Buttons

app.add_handler(
    CallbackQueryHandler(buttons)
)


# =========================================================
# START BOT
# =========================================================

logger.info("Bot starting...")

logger.info(
    "CHANNEL_ID configured: %s",
    bool(CHANNEL_ID)
)

app.run_polling()

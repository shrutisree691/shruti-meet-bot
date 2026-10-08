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
# CHANNEL_ID=-100xxxxxxxxxxxx
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()

DB = "members.db"


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


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


def save(user):
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
        user.id,
        user.username or "",
        user.first_name or "",
        user.last_name or "",
    ))

    c.commit()
    c.close()


def set_status(user_id, new_status):
    c = db()

    c.execute("""
        UPDATE members
        SET status=?,
            active=1,
            updated_at=CURRENT_TIMESTAMP
        WHERE user_id=?
    """, (new_status, user_id))

    c.commit()
    c.close()


def set_removed(user_id):
    c = db()

    c.execute("""
        UPDATE members
        SET status='removed',
            active=0,
            updated_at=CURRENT_TIMESTAMP
        WHERE user_id=?
    """, (user_id,))

    c.commit()
    c.close()


def users(status_filter=None):
    c = db()

    query = "SELECT user_id FROM members WHERE active=1"
    args = ()

    if status_filter:
        query += " AND status=?"
        args = (status_filter,)

    rows = c.execute(query, args).fetchall()
    c.close()

    return [row[0] for row in rows]


# =========================================================
# FIRST SCREEN
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save(update.effective_user)

    await update.message.reply_text(
        "🌸 Welcome!\n\n"
        "I’m Miss Shruti’s Assistant ❤️\n\n"
        "I’m here to help you with her private channel and "
        "guide you through the available options.\n\n"
        "If you’re genuinely interested, please choose an option "
        "below and I’ll guide you through the next step. 😊\n\n"
        "Please be respectful and genuine — time-wasters may be removed. ❤️",
        reply_markup=main_menu(),
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save(update.effective_user)

    await update.message.reply_text(
        "Please choose an option below. ❤️",
        reply_markup=main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Use /start or /status to update your interest."
    )


# =========================================================
# INTERESTED — SECOND SCREEN
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
# REMOVE USER FROM CHANNEL
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

            logger.error(
                "Bot does not have can_restrict_members permission."
            )

            return (
                False,
                "Bot does not have permission to remove members."
            )

        await bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )

        logger.info(
            "User %s removed from channel %s",
            user_id,
            chat_id
        )

        try:

            await bot.unban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                only_if_banned=True
            )

        except Exception:

            logger.exception(
                "User was removed but unban failed."
            )

        return True, None

    except Exception as e:

        logger.exception(
            "Failed to remove user %s from channel.",
            user_id
        )

        return False, str(e)


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
# FINANCIAL REASONS
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

    save(query.from_user)

    user_id = query.from_user.id


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


    elif query.data == "financial":

        await financial_message(query)


    elif query.data == "outside_bangalore":

        await outside_bangalore_message(query)


    elif query.data == "outside_city":

        await outside_city_message(query)


    elif query.data == "ready":

        await ready_message(query)


    elif query.data == "remove":

        await remove_and_reply(
            query,
            context,
            user_id
        )


# =========================================================
# ADMIN
# =========================================================

def is_admin(update: Update):

    return update.effective_user.id == ADMIN_ID


async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):

        return await update.message.reply_text(
            "Admin only."
        )

    c = db()

    result = c.execute("""
        SELECT
            COUNT(*),
            SUM(status='interested'),
            SUM(status='not_interested'),
            SUM(status='unknown'),
            SUM(status='ready_to_confirm')
        FROM members
        WHERE active=1
    """).fetchone()

    c.close()

    await update.message.reply_text(
        f"📊 Stats\n\n"
        f"👥 Registered: {result[0] or 0}\n"
        f"❤️ Interested: {result[1] or 0}\n"
        f"❌ Not Interested: {result[2] or 0}\n"
        f"❤️ Ready: {result[4] or 0}\n"
        f"❔ No status: {result[3] or 0}"
    )


async def members(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):

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

    output = ["👥 Members\n"]

    for i, (
        uid,
        first,
        last,
        username,
        member_status
    ) in enumerate(rows, 1):

        name = " ".join(
            x for x in (first, last)
            if x
        ) or "Unknown"

        if member_status == "interested":
            icon = "❤️"

        elif member_status == "not_interested":
            icon = "❌"

        elif member_status == "ready_to_confirm":
            icon = "✅"

        else:
            icon = "❔"

        output.append(
            f"{i}. {icon} {name} — "
            f"@{username if username else 'no_username'} — {uid}"
        )

    await update.message.reply_text(
        "\n".join(output)[:4000]
    )


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

    c = db()

    row = c.execute("""
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

    if not row:

        return await update.message.reply_text(
            "Member not found."
        )

    (
        uid,
        first,
        last,
        username,
        member_status,
        active,
        created,
        updated,
    ) = row

    name = " ".join(
        x for x in (first, last)
        if x
    ) or "Unknown"

    await update.message.reply_text(
        f"👤 Member\n\n"
        f"Name: {name}\n"
        f"Username: @{username if username else 'none'}\n"
        f"ID: {uid}\n"
        f"Status: {member_status}\n"
        f"Active: {'Yes' if active else 'No'}\n"
        f"Registered: {created}\n"
        f"Updated: {updated}"
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

    for user_id in users():

        try:

            await context.bot.send_message(
                user_id,
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

async def interested(
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

    sent = 0
    failed = 0

    for user_id in users("interested"):

        try:

            await context.bot.send_message(
                user_id,
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
# APPLICATION
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

logger.info("Bot starting...")

logger.info(
    "CHANNEL_ID configured: %s",
    bool(CHANNEL_ID)
)

app.run_polling()

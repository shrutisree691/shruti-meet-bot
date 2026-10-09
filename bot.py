import os
import io
import csv
import sqlite3
import logging
import asyncio
import shutil
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters,
)

# ---------------- SETTINGS ----------------
TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
ADMIN_IDS = {int(x.strip()) for x in os.environ.get('ADMIN_IDS', str(ADMIN_ID)).split(',') if x.strip().isdigit()}
ADMIN_IDS.add(ADMIN_ID)
BACKUP_DIR = os.environ.get('BACKUP_DIR', 'backups')
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
# Configure GROUP_ID in Railway. Multiple groups are also supported via GROUP_IDS.
_group_values = os.environ.get("GROUP_IDS", os.environ.get("GROUP_ID", "")).split(",")
GROUP_IDS = []
for _value in _group_values:
    _value = _value.strip()
    if _value and _value not in GROUP_IDS:
        GROUP_IDS.append(_value)
DB = os.environ.get("DB_PATH", "members.db")
GROUP_DAILY_MESSAGE = "F21 HERE - REAL MEET AVAILABLE - BANGALORE\nDM @SHRUTI23OFFICIAL FOR DETAILS"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DETAILS_TEXT = '''𝐅𝐨𝐫 𝐓𝐡𝐨𝐬𝐞 𝐖𝐡𝐨 𝐀𝐩𝐩𝐫𝐞𝐜𝐢𝐚𝐭𝐞
𝐐𝐮𝐚𝐥𝐢𝐭𝐲 • 𝐂𝐨𝐧𝐧𝐞𝐜𝐭𝐢𝐨𝐧 • 𝐃𝐢𝐬𝐜𝐫𝐞𝐭𝐢𝐨𝐧
╰━❀🌹━━━━━━━━━━━━🌹❀━╯

✨ Hi, I'm 21, based in HSR Layout, Bangalore, and working in the corporate sector. ✨

💕 𝐅𝐞𝐦𝐢𝐧𝐢𝐧𝐞 • 𝐄𝐥𝐞𝐠𝐚𝐧𝐭 • 𝐖𝐚𝐫𝐦 • 𝐇𝐲𝐠𝐢𝐞𝐧𝐢𝐜 • 𝐏𝐥𝐚𝐲𝐟𝐮𝐥 • 𝐄𝐚𝐬𝐲 𝐭𝐨 𝐂𝐨𝐧𝐧𝐞𝐜𝐭 ❤️

Good talks, genuine chemistry, romantic moments, playful foreplay, and an intimate connection that feels natural and exciting. I enjoy creating a warm, passionate atmosphere where we can relax, connect, and leave with a smile. ❤️‍🔥✨

╔══════ 🌹 𝐑𝐚𝐭𝐞𝐬 🌹 ══════╗
💖 1 Hour   ┇ ₹21K (Single Session)
💖 2 Hours  ┇ ₹30K (Double Session)
💖 3 Hours  ┇ ₹35K (Extended Session)
💖 6 Hours  ┇ ₹50K (Quality Time)
💖 8 Hours  ┇ ₹55K (Elite Session)
❤️12 Hours┇ ₹70K (Full Night)
╚═════════════════════╝

✨ Relaxed • Unhurried • Exclusive ✨
🌹 Quality time assured — no rush, no stress, GFE experience, and a comfortable atmosphere. 🌹

═════ ❀ 𝐌𝐞𝐞𝐭𝐢𝐧𝐠 𝐃𝐞𝐭𝐚𝐢𝐥𝐬 ❀ ════
📍 ❥ Outcalls only (Your Home / Hotel)
📍 ❥ I do not have a private place available
🏍 ❥ Exact Rapido fare + advance payment required before the meeting

═════ ❀ 𝐁𝐨𝐨𝐤𝐢𝐧𝐠 𝐏𝐨𝐥𝐢𝐜𝐲 ❀ ═════
🔐 ❥ ₹1,000 advance for booking confirmation
🔐 ❥ Remaining payment can be made after we meet, before we begin
🔐 ❥ Serious enquiries only. If I feel you're only here to chat or waste time, I may block you.
🔐 ❥ The advance confirms a genuine booking and helps avoid wasting time for both of us. 😊

════════ ❀ 𝐏𝐡𝐨𝐭𝐨𝐬 ❀ ════════
📸 ❥ Recent pictures (without face) can be shared initially
📸 ❥ Face pictures are shared after booking confirmation for privacy reasons

═══ ❀ 𝐂𝐨𝐦𝐟𝐨𝐫𝐭 & 𝐁𝐨𝐮𝐧𝐝𝐚𝐫𝐢𝐞𝐬 ❀ ═══
🤍 ✔️ Protection is mandatory (Condom is a must)
🤍 ✔️ No anal / No BDSM
🤍 ✔️ No rough play or painful acts
🤍 ✔️ No aggressive fingering, biting, choking, slapping, or hair pulling
🤍 ✔️ Please be gentle and respectful throughout the meet ❤️
🤍 ✔️ Mutual comfort, consent, and hygiene are important to me
🤍 ✔️ If I say "slow down," or "I'm uncomfortable," I expect it to be respected immediately
🌹 Please book only if you're comfortable respecting these boundaries.

💕 Looking for more than just physical intimacy—think of it as a warm, relaxing, enjoyable experience where we both leave smiling.✨

🌸 It's Me! 🔞
Bust • Waist • Hips
34B • 28 • 36

📢 Feedbacks:
https://t.me/+Jan_CAExO9ZlZDVl

✅ Video-call verified by admins of multiple Bangalore Telegram groups.
🌹 Real meet proofs and genuine reviews available on my channel.

📩 If you're comfortable with my rates, please send:
💌 Duration
💌 Preferred Date & Time
💌 Meeting Location (Your Home / Hotel)

╭━━━━━━━━━━━━━━━━━━━━━━╮
💝 "Get ready for the experience you've been waiting for." ✨
╰━━━━━━━━━━━━━━━━━━━━━━╯
༺❤️༻────────────༺❤️༻

shruti meet charges and details'''

# ---------------- DATABASE ----------------
def db():
    # Apply additive, backward-compatible schema migrations.
    parent = os.path.dirname(os.path.abspath(DB))
    os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute('''CREATE TABLE IF NOT EXISTS members (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT,
        status TEXT DEFAULT 'unknown', active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
        reminder_started_at TEXT DEFAULT '', reminder_count INTEGER DEFAULT 0,
        reminder_stopped INTEGER DEFAULT 0, reminder_last_sent_date TEXT DEFAULT '',
        reminder_last_attempt_date TEXT DEFAULT '')''')
    member_columns = {r['name'] for r in conn.execute('PRAGMA table_info(members)').fetchall()}
    if 'last_seen_at' not in member_columns:
        # SQLite cannot add a CURRENT_TIMESTAMP default through ALTER TABLE.
        conn.execute("ALTER TABLE members ADD COLUMN last_seen_at TEXT DEFAULT ''")
        conn.execute("UPDATE members SET last_seen_at=CURRENT_TIMESTAMP WHERE last_seen_at='' OR last_seen_at IS NULL")
    member_columns = {r['name'] for r in conn.execute('PRAGMA table_info(members)').fetchall()}
    reminder_columns = {
        'reminder_started_at': "TEXT DEFAULT ''",
        'reminder_count': 'INTEGER DEFAULT 0',
        'reminder_stopped': 'INTEGER DEFAULT 0',
        'reminder_last_sent_date': "TEXT DEFAULT ''",
        'reminder_last_attempt_date': "TEXT DEFAULT ''",
    }
    for column, definition in reminder_columns.items():
        if column not in member_columns:
            conn.execute(f'ALTER TABLE members ADD COLUMN {column} {definition}')
    # Existing eligible members start a fresh seven-reminder window after upgrade.
    conn.execute("UPDATE members SET reminder_started_at=CURRENT_TIMESTAMP WHERE active=1 AND status IN ('unknown','interested','meet_later_financial','meet_later_outside_bangalore','interested_outside_city') AND (reminder_started_at='' OR reminder_started_at IS NULL)")
    conn.execute('''CREATE TABLE IF NOT EXISTS booking_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        username TEXT, display_name TEXT, preferred_datetime TEXT, duration TEXT,
        location TEXT, notes TEXT DEFAULT '', status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        reminder_at TEXT, reminder_sent INTEGER DEFAULT 0, admin_note TEXT DEFAULT '', slot_id INTEGER)''')
    columns = {r['name'] for r in conn.execute('PRAGMA table_info(booking_requests)').fetchall()}
    if 'slot_id' not in columns:
        conn.execute('ALTER TABLE booking_requests ADD COLUMN slot_id INTEGER')
    conn.execute('''CREATE TABLE IF NOT EXISTS availability_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, slot_datetime TEXT NOT NULL,
        duration TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'available',
        booked_request_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id INTEGER, action TEXT NOT NULL,
        target_type TEXT DEFAULT '', target_id TEXT DEFAULT '', details TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS group_daily_post_log (
        group_id TEXT PRIMARY KEY, last_post_date TEXT NOT NULL DEFAULT '',
        message_id INTEGER, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS app_settings (
        setting_key TEXT PRIMARY KEY, setting_value TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS rate_limits (
        user_id INTEGER NOT NULL, action TEXT NOT NULL, last_at REAL NOT NULL,
        PRIMARY KEY(user_id, action))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS rate_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, created_at REAL NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS notification_preferences (
        category TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 1)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    for category in ('status', 'booking', 'errors', 'broadcast'):
        conn.execute('INSERT OR IGNORE INTO notification_preferences(category,enabled) VALUES(?,1)', (category,))
    conn.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES(1)')
    conn.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES(2)')
    conn.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES(3)')
    conn.commit()
    try: os.chmod(DB, 0o600)
    except OSError: pass
    return conn


def audit(actor_id, action, target_type='', target_id='', details=''):
    try:
        conn = db()
        conn.execute('INSERT INTO audit_log(actor_id,action,target_type,target_id,details) VALUES(?,?,?,?,?)',
                     (actor_id, action[:100], target_type[:100], str(target_id)[:100], details[:1000]))
        conn.commit(); conn.close()
    except Exception:
        logger.exception('Could not write audit log')


def pref_enabled(category):
    conn = db()
    row = conn.execute('SELECT enabled FROM notification_preferences WHERE category=?', (category,)).fetchone()
    conn.close()
    return bool(row['enabled']) if row else True


def allow_action(user_id, action, limit_seconds=2):
    # Simple persistent per-user action cooldown to dampen spam/double clicks.
    now = time.time()
    conn = db()
    row = conn.execute('SELECT last_at FROM rate_limits WHERE user_id=? AND action=?', (user_id, action)).fetchone()
    if row and now - row['last_at'] < limit_seconds:
        conn.close()
        return False
    conn.execute('DELETE FROM rate_events WHERE created_at < ?', (now - 60,))
    count = conn.execute('SELECT COUNT(*) n FROM rate_events WHERE user_id=? AND created_at>=?', (user_id, now - 60)).fetchone()['n']
    if count >= 20:
        conn.close()
        return False
    conn.execute('INSERT INTO rate_events(user_id,created_at) VALUES(?,?)', (user_id, now))
    conn.execute('INSERT INTO rate_limits(user_id,action,last_at) VALUES(?,?,?) '
                 'ON CONFLICT(user_id,action) DO UPDATE SET last_at=excluded.last_at', (user_id, action, now))
    conn.commit()
    conn.close()
    return True



def save_user(user):
    conn = db()
    old = conn.execute('SELECT user_id FROM members WHERE user_id=?', (user.id,)).fetchone()
    conn.execute('''INSERT INTO members(user_id,username,first_name,last_name,reminder_started_at)
        VALUES(?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username, first_name=excluded.first_name,
        last_name=excluded.last_name, active=1, updated_at=CURRENT_TIMESTAMP,
        last_seen_at=CURRENT_TIMESTAMP''',
        (user.id, user.username or '', user.first_name or '', user.last_name or ''))
    conn.execute("UPDATE members SET reminder_started_at=CURRENT_TIMESTAMP WHERE user_id=? AND (reminder_started_at='' OR reminder_started_at IS NULL) AND status IN ('unknown','interested','meet_later_financial','meet_later_outside_bangalore','interested_outside_city') AND reminder_stopped=0", (user.id,))
    conn.commit()
    conn.close()
    return old is not None


def set_status(user_id, status):
    # Reminders continue through interest/booking stages and stop only after
    # an explicit opt-out, admin-confirmed advance, completed booking, or removal.
    eligible = {
        'unknown', 'interested', 'meet_later_financial',
        'meet_later_outside_bangalore', 'interested_outside_city',
        'ready_to_confirm', 'booking_pending', 'booking_approved', 'booking_rejected'
    }
    stop_statuses = {'not_interested', 'advance_received', 'booking_completed', 'removed', 'removal_failed'}
    conn = db()
    old = conn.execute('SELECT status, reminder_stopped FROM members WHERE user_id=?', (user_id,)).fetchone()
    if status in stop_statuses:
        conn.execute('UPDATE members SET status=?, active=?, reminder_stopped=1, updated_at=CURRENT_TIMESTAMP WHERE user_id=?', (status, 0 if status == 'removed' else 1, user_id))
    elif status in eligible:
        restart = bool(old and (old['status'] in stop_statuses or old['reminder_stopped']))
        if restart:
            conn.execute('''UPDATE members SET status=?, active=1, reminder_started_at=CURRENT_TIMESTAMP,
                reminder_count=0, reminder_stopped=0, reminder_last_sent_date='',
                reminder_last_attempt_date='', updated_at=CURRENT_TIMESTAMP WHERE user_id=?''', (status, user_id))
        else:
            conn.execute("UPDATE members SET status=?, active=1, reminder_stopped=0, reminder_started_at=CASE WHEN reminder_started_at='' OR reminder_started_at IS NULL THEN CURRENT_TIMESTAMP ELSE reminder_started_at END, updated_at=CURRENT_TIMESTAMP WHERE user_id=?", (status, user_id))
    else:
        conn.execute('UPDATE members SET status=?, active=1, reminder_stopped=1, updated_at=CURRENT_TIMESTAMP WHERE user_id=?', (status, user_id))
    conn.commit(); conn.close()
    audit(user_id, 'status_changed', 'member', user_id, status)


def get_users(status=None):
    conn = db()
    if status:
        rows = conn.execute('SELECT user_id FROM members WHERE active=1 AND status=?', (status,)).fetchall()
    else:
        rows = conn.execute('SELECT user_id FROM members WHERE active=1').fetchall()
    conn.close()
    return [r['user_id'] for r in rows]


def name_for(user):
    return ' '.join(x for x in [user.first_name, user.last_name] if x) or 'Unknown'


def is_admin(update):
    return bool(update.effective_user and update.effective_user.id in ADMIN_IDS)


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('❤️ I’m Interested', callback_data='interested')],
        [InlineKeyboardButton('❌ I’m Not Interested', callback_data='not_interested')],
        [InlineKeyboardButton('🌹 Shruti — Meet Charges & Details', callback_data='meet_details')],
        [InlineKeyboardButton('💬 Contact Admin', url='https://t.me/shruti23official')],
    ])


def interested_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('❤️ I’m ready to confirm the meet now', callback_data='ready')],
        [InlineKeyboardButton('💰 Meet later — financial reasons', callback_data='financial')],
        [InlineKeyboardButton('📍 Meet later — currently outside Bangalore', callback_data='outside_bangalore')],
        [InlineKeyboardButton('✈️ Interested in meeting outside Bangalore', callback_data='outside_city')],
        [InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')],
    ])


def confirmation_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('❤️ Ready to confirm & stay in channel', callback_data='ready')],
        [InlineKeyboardButton('⏳ Not ready — remove me from channel', callback_data='remove')],
        [InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')],
    ])


def duration_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('1 hour', callback_data='duration|1 hour'), InlineKeyboardButton('2 hours', callback_data='duration|2 hours')],
        [InlineKeyboardButton('3 hours', callback_data='duration|3 hours'), InlineKeyboardButton('6 hours', callback_data='duration|6 hours')],
        [InlineKeyboardButton('8 hours', callback_data='duration|8 hours'), InlineKeyboardButton('12 hours', callback_data='duration|12 hours')],
        [InlineKeyboardButton('⬅️ Cancel', callback_data='booking_cancel')],
    ])


def admin_request_keyboard(request_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Approve', callback_data=f'req|approve|{request_id}'), InlineKeyboardButton('❌ Reject', callback_data=f'req|reject|{request_id}')],
        [InlineKeyboardButton('📝 Ask for details', callback_data=f'req|ask|{request_id}')],
    ])

# ---------------- REMINDERS ----------------
async def reminder_worker(app):
    while True:
        try:
            conn = db()
            rows = conn.execute("SELECT id,user_id,preferred_datetime,reminder_at FROM booking_requests WHERE status='approved' AND reminder_sent=0 AND reminder_at IS NOT NULL").fetchall()
            conn.close()
            now_local = datetime.now(ZoneInfo('Asia/Kolkata'))
            for row in rows:
                try:
                    due = datetime.fromisoformat(row['reminder_at'])
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=ZoneInfo('Asia/Kolkata'))
                    if due > now_local:
                        continue
                    await app.bot.send_message(row['user_id'], f"🔔 Reminder: your booking request #{row['id']} is coming up ({row['preferred_datetime']}). If anything changed, please contact @shruti23official.")
                    conn = db()
                    conn.execute("UPDATE booking_requests SET reminder_sent=1,updated_at=CURRENT_TIMESTAMP WHERE id=? AND reminder_sent=0", (row['id'],))
                    conn.commit(); conn.close()
                except Exception:
                    logger.exception('Reminder send failed for request %s; it will be retried', row['id'])
        except Exception:
            logger.exception('Reminder worker failed')
        await asyncio.sleep(60)


def interest_reminder_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('❤️ Ready to Confirm', callback_data='reminder_ready')],
        [InlineKeyboardButton('💬 Show My Options', callback_data='reminder_options')],
        [InlineKeyboardButton('❌ Not Interested', callback_data='reminder_not_interested')],
    ])


async def interest_reminder_worker(app):
    """Send one private reminder daily at 11:00 Asia/Kolkata until opt-out or admin-confirmed advance."""
    tz = ZoneInfo('Asia/Kolkata')
    eligible_statuses = (
        'unknown', 'interested', 'meet_later_financial',
        'meet_later_outside_bangalore', 'interested_outside_city',
        'ready_to_confirm', 'booking_pending', 'booking_approved', 'booking_rejected'
    )
    while True:
        try:
            now = datetime.now(tz)
            today = now.date().isoformat()
            if now.hour == 11 and now.minute < 5:
                conn = db()
                placeholders = ','.join('?' for _ in eligible_statuses)
                rows = conn.execute(
                    f"""SELECT user_id, status, reminder_count, reminder_last_sent_date,
                               reminder_last_attempt_date
                        FROM members
                        WHERE active=1 AND reminder_stopped=0
                          AND status IN ({placeholders})""", eligible_statuses
                ).fetchall()
                conn.close()
                for row in rows:
                    user_id = row['user_id']
                    if row['reminder_last_attempt_date'] == today or row['reminder_last_sent_date'] == today:
                        continue
                    conn = db()
                    conn.execute('UPDATE members SET reminder_last_attempt_date=? WHERE user_id=? AND reminder_stopped=0', (today, user_id))
                    conn.commit(); conn.close()
                    message = (
                        'Hi! Miss Bot here 🌸\n\n'
                        'Real meet availability with Shruti may be available today in Bangalore. ❤️\n\n'
                        'If you are interested, choose “Ready to Confirm” and contact @shruti23official '
                        'to discuss booking and advance payment. If you need voice confirmation from Shruti, '
                        'please contact her directly.\n\n'
                        'You will receive at most one reminder per day. Reminders stop when you choose '
                        '“Not Interested” or the admin confirms your advance has been received.'
                    )
                    try:
                        await app.bot.send_message(user_id, message, reply_markup=interest_reminder_keyboard())
                        conn = db()
                        conn.execute('UPDATE members SET reminder_count=reminder_count+1, reminder_last_sent_date=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND reminder_stopped=0', (today, user_id))
                        conn.commit(); conn.close()
                        audit(0, 'interest_reminder_sent', 'member', user_id, f'daily reminder count {row["reminder_count"] + 1}')
                    except Forbidden:
                        conn = db()
                        conn.execute('UPDATE members SET reminder_stopped=1,updated_at=CURRENT_TIMESTAMP WHERE user_id=?', (user_id,))
                        conn.commit(); conn.close()
                        logger.info('Stopping reminders for %s because private messages are unavailable', user_id)
                    except Exception:
                        logger.exception('Interest reminder failed for user %s', user_id)
        except Exception:
            logger.exception('Interest reminder worker failed')
        await asyncio.sleep(60)


async def backup_worker(app):
    # Create a daily SQLite-consistent backup on persistent storage.
    while True:
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target = os.path.join(BACKUP_DIR, f'members_{stamp}.sqlite3')
            source = sqlite3.connect(DB, timeout=20)
            dest = sqlite3.connect(target)
            source.backup(dest)
            dest.close(); source.close()
            try: os.chmod(target, 0o600)
            except OSError: pass
            files = sorted(Path(BACKUP_DIR).glob('members_*.sqlite3'), key=lambda x: x.stat().st_mtime, reverse=True)
            for old in files[7:]:
                old.unlink(missing_ok=True)
        except Exception:
            logger.exception('Automatic backup failed')
            if pref_enabled('errors'):
                for admin_id in ADMIN_IDS:
                    try: await app.bot.send_message(admin_id, '⚠️ Automatic database backup failed. Check Railway logs and storage configuration.')
                    except Exception: logger.exception('Could not alert admin about backup failure')








        await asyncio.sleep(24 * 60 * 60)


async def group_daily_post_worker(app):
    """Post once per configured group daily at 17:00 Asia/Kolkata.

    The successful post date is saved in SQLite so restarts do not normally
    cause a second post on the same day. The worker retries failed posts during
    the 17:00–17:09 IST window.
    """
    if not GROUP_IDS:
        logger.info('GROUP_ID/GROUP_IDS not configured; daily group posting disabled')
        return

    tz = ZoneInfo('Asia/Kolkata')
    while True:
        try:
            now = datetime.now(tz)
            if now.hour == 17 and now.minute < 10:
                today = now.date().isoformat()
                for group_id in GROUP_IDS:
                    conn = db()
                    row = conn.execute(
                        'SELECT last_post_date FROM group_daily_post_log WHERE group_id=?',
                        (group_id,),
                    ).fetchone()
                    conn.close()
                    if row and row['last_post_date'] == today:
                        continue
                    try:
                        sent = await app.bot.send_message(
                            chat_id=group_id,
                            text=GROUP_DAILY_MESSAGE,
                        )
                        conn = db()
                        conn.execute(
                            """INSERT INTO group_daily_post_log(group_id,last_post_date,message_id,updated_at)
                               VALUES(?,?,?,CURRENT_TIMESTAMP)
                               ON CONFLICT(group_id) DO UPDATE SET
                                 last_post_date=excluded.last_post_date,
                                 message_id=excluded.message_id,
                                 updated_at=CURRENT_TIMESTAMP""",
                            (group_id, today, sent.message_id),
                        )
                        conn.commit()
                        conn.close()
                        audit(0, 'daily_group_post_sent', 'group', group_id, f'date={today}; message_id={sent.message_id}')
                        logger.info('Daily group post sent to %s for %s', group_id, today)
                    except Exception as error:
                        logger.exception('Daily group post failed for %s; will retry during posting window', group_id)
                        for admin_id in ADMIN_IDS:
                            try:
                                await app.bot.send_message(
                                    chat_id=admin_id,
                                    text=f'⚠️ Daily group post failed for group {group_id}: {type(error).__name__}. Check group ID and bot posting permissions.',
                                )
                            except Exception:
                                logger.exception('Could not alert admin about group post failure')
        except Exception:
            logger.exception('Daily group post worker failed')
        await asyncio.sleep(60)


async def post_init(app):
    app.create_task(reminder_worker(app))
    app.create_task(interest_reminder_worker(app))
    app.create_task(backup_worker(app))
    app.create_task(group_daily_post_worker(app))


# ---------------- USER COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    returning = save_user(update.effective_user)
    greeting = 'Welcome back' if returning else 'Welcome'
    await update.message.reply_text(
        f'😎 {greeting}! I’m Miss Bot! 🤖🌸\n\n'
        'I’m Miss Shruti’s little AI Assistant ❤️\n\n'
        'Choose an option below to see details or update your interest. 😊',
        reply_markup=main_menu())


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    await update.message.reply_text('Please choose an option below. ❤️', reply_markup=main_menu())


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Use /start or /status to update your interest. Use /help for help.')

# ---------------- CHANNEL REMOVAL ----------------
async def remove_from_channel(bot, user_id):
    if not CHANNEL_ID:
        return False, 'CHANNEL_ID is not configured.'
    try:
        chat_id = int(CHANNEL_ID)
        me = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id, me.id)
        if not getattr(bot_member, 'can_restrict_members', False):
            return False, 'Bot does not have permission to restrict members.'
        await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        try:
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
        except Exception:
            logger.exception('Removed user but could not unban them')
        return True, None
    except Exception as exc:
        logger.exception('Failed to remove user %s from channel', user_id)
        return False, str(exc)


async def remove_and_reply(query, context, user_id):
    ok, error = await remove_from_channel(context.bot, user_id)
    conn = db()
    if ok:
        conn.execute("UPDATE members SET status='removed',active=0,updated_at=CURRENT_TIMESTAMP WHERE user_id=?", (user_id,))
        msg = '❌ No problem 😊\n\nYou’ve been removed from the channel. If you want to join again later, contact @shruti23official. ❤️'
    else:
        conn.execute("UPDATE members SET status='removal_failed',updated_at=CURRENT_TIMESTAMP WHERE user_id=?", (user_id,))
        msg = '❌ I couldn’t remove you automatically. Please contact @shruti23official for help. ❤️'
        await context.bot.send_message(ADMIN_ID, f'⚠️ Channel removal failed for user ID {user_id}. Error: {error}')
    conn.commit(); conn.close()
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')]]))

# ---------------- BOOKING FLOW ----------------
async def begin_booking(query, context):
    conn = db()
    slots = conn.execute("SELECT id,slot_datetime,duration FROM availability_slots WHERE status='available'").fetchall()
    conn.close()
    now_local = datetime.now(ZoneInfo('Asia/Kolkata'))
    valid_slots = []
    for row in slots:
        try:
            parsed_slot = datetime.strptime(row['slot_datetime'], '%d %b %Y, %I:%M %p').replace(tzinfo=ZoneInfo('Asia/Kolkata'))
            if parsed_slot > now_local:
                valid_slots.append((parsed_slot, row))
        except ValueError:
            continue
    slots = [row for _, row in sorted(valid_slots, key=lambda item: item[0])][:20]
    context.user_data['booking_form'] = {'step': 'datetime'}
    if slots:
        rows = [[InlineKeyboardButton(f"{r['slot_datetime']} · {r['duration']}", callback_data=f"slot|{r['id']}")] for r in slots]
        rows.append([InlineKeyboardButton('Enter another preferred time', callback_data='booking_manual')])
        rows.append([InlineKeyboardButton('Cancel', callback_data='booking_cancel')])
        return await query.edit_message_text('❤️ Choose an available time. Your request is not confirmed until approved.', reply_markup=InlineKeyboardMarkup(rows))
    await query.edit_message_text(
        '❤️ Let’s prepare your booking request. This is a request only; it is not confirmed until the admin approves it.\n\n'
        'First, send your preferred date and time in this format: 25 Oct 2026, 07:30 PM. This format enables automatic reminders.',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='booking_cancel')]])
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return
    if user.id not in ADMIN_IDS and not allow_action(user.id, 'text_message', 0.35):
        return await update.message.reply_text('Please wait a moment before sending another message.')
    # Booking form steps for regular users
    form = context.user_data.get('booking_form')
    if form:
        answer = update.message.text.strip()
        if answer.startswith('/'):
            return
        if form['step'] == 'datetime':
            if len(answer) < 4 or len(answer) > 100:
                return await update.message.reply_text('Please send a date and time, for example: 25 Oct, 7:30 PM.')
            form['preferred_datetime'] = answer
            form['slot_id'] = None
            form['step'] = 'location'
            return await update.message.reply_text('📍 Where would you prefer to meet? Please provide a general location or area (do not send a full private address yet).')
        if form['step'] == 'location':
            if len(answer) < 2 or len(answer) > 180:
                return await update.message.reply_text('Please enter a short location or area.')
            form['location'] = answer
            if form.get('slot_id'):
                form['step'] = 'notes'
                return await update.message.reply_text('📝 Any additional notes? Type a short note or “None”. Do not send a full private address or payment details.')
            form['step'] = 'duration'
            return await update.message.reply_text('⏱️ Choose your preferred duration:', reply_markup=duration_menu())
        if form['step'] == 'notes':
            form['notes'] = answer[:500]
            return await finalize_booking(update, context)

    # Admin broadcast confirmation text response
    if is_admin(update) and context.user_data.get('broadcast_draft'):
        return await update.message.reply_text('You have a broadcast draft waiting. Use the confirmation buttons on the draft or /cancelbroadcast to discard it.')


async def finalize_booking(update, context):
    user = update.effective_user
    form = context.user_data.pop('booking_form', None)
    if not form:
        return
    conn = db()
    cur = conn.execute('''INSERT INTO booking_requests(user_id,username,display_name,preferred_datetime,duration,location,notes,slot_id)
        VALUES(?,?,?,?,?,?,?,?)''', (user.id, user.username or '', name_for(user), form['preferred_datetime'], form['duration'], form['location'], form.get('notes', ''), form.get('slot_id')))
    request_id = cur.lastrowid
    conn.commit(); conn.close()
    audit(user.id, 'booking_request_created', 'booking_request', request_id, form['preferred_datetime'])
    set_status(user.id, 'booking_pending')
    admin_text = (
        f'📥 New booking request #{request_id}\n\nName: {name_for(user)}\n'
        f'Username: @{user.username or "none"}\nUser ID: {user.id}\n'
        f'Date/time: {form["preferred_datetime"]}\nDuration: {form["duration"]}\n'
        f'Location/area: {form["location"]}\nNotes: {form.get("notes", "None")}\n\nStatus: Pending admin review'
    )
    try:
        await notify_admin(context, admin_text, category='booking', reply_markup=admin_request_keyboard(request_id))
    except Exception:
        logger.exception('Could not notify admin about request %s', request_id)
        await update.effective_message.reply_text('Your request was saved, but I could not notify the admin. Please contact @shruti23official directly.')
        return
    await update.effective_message.reply_text(
        f'✅ Your request #{request_id} has been sent for review. It is not confirmed yet; wait for an admin response. ❤️',
        reply_markup=main_menu())

# ---------------- BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id







    if user_id not in ADMIN_IDS and not allow_action(user_id, 'callback', 1):
        return await query.answer('Please wait a moment before trying again.', show_alert=True)
    await query.answer()
    save_user(query.from_user)
    data = query.data or ''

    if data == 'reminder_ready':
        set_status(user_id, 'ready_to_confirm')
        await notify_admin(context, f'✅ Confirmed from reminder: {name_for(query.from_user)} (@{query.from_user.username or "none"}), ID {user_id}')
        context.user_data['awaiting_message_to_shruti'] = True
        return await query.edit_message_text(
            '❤️ Thanks for confirming your interest!\n\n'
            'Would you like to ask or tell Shruti anything? You can type your message here and send it. I’ll pass it on to her. 😊\n\n'
            'For booking or voice confirmation, you can also contact @shruti23official directly.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⏭ Skip and continue to booking', callback_data='shruti_message_skip')],
                [InlineKeyboardButton('💬 Contact @shruti23official', url='https://t.me/shruti23official')],
                [InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')],
            ]),
        )

    if data == 'reminder_not_interested':
        set_status(user_id, 'not_interested')
        await notify_admin(context, f'❌ Opted out from reminder: {name_for(query.from_user)} (@{query.from_user.username or "none"}), ID {user_id}')
        return await remove_and_reply(query, context, user_id)

    if data == 'reminder_options':
        set_status(user_id, 'interested')
        return await query.edit_message_text('Please choose the option that best describes your current situation. ❤️', reply_markup=interested_menu())

    if data == 'back_main':
        context.user_data.pop('booking_form', None)
        context.user_data.pop('awaiting_message_to_shruti', None)
        return await query.edit_message_text('Choose an option below. ❤️', reply_markup=main_menu())

    if data == 'shruti_message_skip':
        context.user_data.pop('awaiting_message_to_shruti', None)
        return await query.edit_message_text(
            'No problem! ❤️ You can contact Shruti directly for booking or voice confirmation.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('📝 Start booking request', callback_data='booking_start')],
                [InlineKeyboardButton('💬 Contact @shruti23official', url='https://t.me/shruti23official')],
                [InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')],
            ]),
        )

    if data == 'meet_details':
        first = DETAILS_TEXT[:3800]
        await query.edit_message_text(first, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')]]))
        for i in range(3800, len(DETAILS_TEXT), 3800):
            await context.bot.send_message(user_id, DETAILS_TEXT[i:i + 3800])
        return

    if data == 'interested':
        set_status(user_id, 'interested')
        await notify_admin(context, f'❤️ User interested: {name_for(query.from_user)} (@{query.from_user.username or "none"}), ID {user_id}')
        return await query.edit_message_text('Aww, nice to know you’re interested! 🥰❤️\n\nChoose the option that best describes your current situation.', reply_markup=interested_menu())

    if data == 'not_interested':
        set_status(user_id, 'not_interested')
        await notify_admin(context, f'❌ Not interested: {name_for(query.from_user)} (@{query.from_user.username or "none"}), ID {user_id}')
        return await remove_and_reply(query, context, user_id)

    if data == 'financial':
        set_status(user_id, 'meet_later_financial')
        await notify_admin(context, f'💰 Meet later — financial reasons: {name_for(query.from_user)}, ID {user_id}')
        text = ('Okay, I understand that. ❤️\n\nShruti keeps her private channel for people genuinely interested in meeting her or who have already met her.\n\n'
                'Please review this channel update: https://t.me/c/3777733349/230\n\nIf you wish to stay in the channel, confirmation is required now. If you are not ready, choose to leave.')
        return await query.edit_message_text(text, reply_markup=confirmation_menu())

    if data == 'outside_bangalore':
        set_status(user_id, 'meet_later_outside_bangalore')
        await notify_admin(context, f'📍 Currently outside Bangalore: {name_for(query.from_user)}, ID {user_id}')
        text = ('Okay, I understand. ❤️\n\nSince you’re currently outside Bangalore, no worries.\n\nPlease review this channel update: https://t.me/c/3777733349/230\n\nIf you wish to stay in the channel, confirmation is required now. If you are not ready, choose to leave.')
        return await query.edit_message_text(text, reply_markup=confirmation_menu())

    if data == 'outside_city':
        set_status(user_id, 'interested_outside_city')
        await notify_admin(context, f'✈️ Interested outside Bangalore: {name_for(query.from_user)}, ID {user_id}')
        text = ('That’s nice to hear. ❤️\n\nPlease review this channel update: https://t.me/c/3777733349/230\n\nFor out-of-city arrangements, contact @shruti23official. If you wish to stay in the channel, confirm below or choose to leave.')
        return await query.edit_message_text(text, reply_markup=confirmation_menu())

    if data == 'ready':
        set_status(user_id, 'ready_to_confirm')
        await notify_admin(context, f'✅ Ready to confirm: {name_for(query.from_user)} (@{query.from_user.username or "none"}), ID {user_id}')
        context.user_data['awaiting_message_to_shruti'] = True
        return await query.edit_message_text(
            '❤️ Perfect! Before booking, would you like to ask or tell Shruti anything?\n\n'
            'Just type your message in the message box and send it here. I’ll let her know. 😊\n\n'
            'If you need voice confirmation from Shruti, please contact @shruti23official directly.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⏭ Skip and continue to booking', callback_data='shruti_message_skip')],
                [InlineKeyboardButton('💬 Contact @shruti23official', url='https://t.me/shruti23official')],
                [InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')],
            ]),
        )

    if data == 'booking_start':
        return await begin_booking(query, context)

    if data == 'booking_cancel':
        context.user_data.pop('booking_form', None)
        audit(user_id, 'booking_form_cancelled')
        return await query.edit_message_text('Booking request cancelled. You can start again any time. ❤️', reply_markup=main_menu())

    if data == 'booking_manual':
        context.user_data['booking_form'] = {'step': 'datetime'}
        return await query.edit_message_text('Send your preferred date and time (example: 25 Oct 2026, 07:30 PM).', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='booking_cancel')]]))

    if data.startswith('slot|'):
        form = context.user_data.get('booking_form')
        if not form:
            return await query.edit_message_text('Please start a new booking request.', reply_markup=main_menu())
        try:
            slot_id = int(data.split('|', 1)[1])
        except ValueError:
            return await query.edit_message_text('Invalid slot. Please start again.', reply_markup=main_menu())
        conn = db(); slot = conn.execute("SELECT * FROM availability_slots WHERE id=? AND status='available'", (slot_id,)).fetchone(); conn.close()
        if not slot:
            context.user_data.pop('booking_form', None)
            return await query.edit_message_text('That slot is no longer available. Please start again.', reply_markup=main_menu())
        form.update({'preferred_datetime': slot['slot_datetime'], 'duration': slot['duration'], 'slot_id': slot_id, 'step': 'location'})
        return await query.edit_message_text('📍 Please enter a general meeting area. Do not send a full private address yet.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='booking_cancel')]]))

    if data.startswith('duration|'):
        form = context.user_data.get('booking_form')
        if not form or form.get('step') != 'duration':
            return await query.edit_message_text('Please start a new booking request from the menu.', reply_markup=main_menu())
        form['duration'] = data.split('|', 1)[1]
        form['step'] = 'notes'
        return await query.edit_message_text('📝 Any additional notes? Send a short message in chat, or type “None”. Do not send payment details or a full private address here.')

    if data.startswith('req|'):
        if not is_admin(update):
            return await query.edit_message_text('Admin only.')
        _, action, request_id_s = data.split('|', 2)
        request_id = int(request_id_s)
        conn = db()
        req = conn.execute('SELECT * FROM booking_requests WHERE id=?', (request_id,)).fetchone()
        if not req:
            conn.close()
            return await query.edit_message_text('Request not found.')
        if action == 'approve':
            if req['status'] not in ('pending', 'needs_details'):
                conn.close()
                return await query.edit_message_text(f"This request was already processed (status: {req['status']}).")
            # Reserve a selected slot atomically to prevent double booking.
            if req['slot_id']:
                conn.execute('BEGIN IMMEDIATE')
                slot_update = conn.execute("UPDATE availability_slots SET status='booked',booked_request_id=? WHERE id=? AND status='available'", (request_id, req['slot_id']))
                if slot_update.rowcount != 1:
                    conn.rollback(); conn.close()
                    return await query.edit_message_text('⚠️ This availability slot was already taken. Please review the request and offer another time.')
            reminder_at = None
            try:
                parsed = datetime.strptime(req['preferred_datetime'], '%d %b %Y, %I:%M %p').replace(tzinfo=ZoneInfo('Asia/Kolkata'))
                reminder_at = (parsed - timedelta(hours=2)).isoformat(timespec='minutes')
            except ValueError:
                pass
            request_update = conn.execute("UPDATE booking_requests SET status='approved',reminder_at=?,reminder_sent=0,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('pending','needs_details')", (reminder_at, request_id))
            if request_update.rowcount != 1:
                conn.rollback(); conn.close()
                return await query.edit_message_text('This request has already been processed.')
            conn.commit(); conn.close()
            set_status(req['user_id'], 'booking_approved')
            audit(user_id, 'booking_approved', 'booking_request', request_id, req['preferred_datetime'])
            await context.bot.send_message(req['user_id'], f'✅ Your booking request #{request_id} has been approved by the admin. Please contact @shruti23official to confirm final arrangements. ❤️')
            return await query.edit_message_text(f'✅ Request #{request_id} approved. ' + ('A reminder was scheduled for two hours before the date/time.' if reminder_at else 'Automatic reminder was not scheduled because the date format could not be recognized.'), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏁 Mark completed', callback_data=f'req|complete|{request_id}')]]))
        if action == 'reject':
            if req['status'] not in ('pending', 'needs_details'):
                conn.close()
                return await query.edit_message_text(f"This request was already processed (status: {req['status']}).")
            conn.execute("UPDATE booking_requests SET status='rejected',updated_at=CURRENT_TIMESTAMP WHERE id=?", (request_id,))
            conn.commit(); conn.close()
            if req['slot_id']:
                conn = db(); conn.execute("UPDATE availability_slots SET status='available',booked_request_id=NULL WHERE id=? AND booked_request_id=?", (req['slot_id'], request_id)); conn.commit(); conn.close()
            set_status(req['user_id'], 'booking_rejected')
            audit(user_id, 'booking_rejected', 'booking_request', request_id)
            await context.bot.send_message(req['user_id'], f'❌ Your booking request #{request_id} was not approved. You may contact @shruti23official if you have questions.')
            return await query.edit_message_text(f'❌ Request #{request_id} rejected. User notified.')
        if action == 'complete':
            if req['status'] != 'approved':
                conn.close()
                return await query.edit_message_text(f"This request cannot be marked completed from status: {req['status']}")
            updated = conn.execute("UPDATE booking_requests SET status='completed',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='approved'", (request_id,))
            conn.commit(); conn.close()
            if updated.rowcount != 1:
                return await query.edit_message_text('This request has already been processed.')
            set_status(req['user_id'], 'booking_completed')
            audit(user_id, 'booking_completed', 'booking_request', request_id)
            return await query.edit_message_text(f'✅ Request #{request_id} marked completed.')
        if action == 'ask':
            audit(user_id, 'booking_followup_requested', 'booking_request', request_id)
            conn.execute("UPDATE booking_requests SET status='needs_details',updated_at=CURRENT_TIMESTAMP WHERE id=?", (request_id,))
            conn.commit(); conn.close()
            context.user_data['ask_details_request_id'] = request_id
            return await query.edit_message_text(f'📝 Send the follow-up question to the user for request #{request_id} as your next message, or use /cancelask to cancel.')

# ---------------- ADMIN NOTIFICATIONS ----------------
async def notify_admin(context, message, category='status', reply_markup=None):
    if not pref_enabled(category):
        return
    bot = context.bot if context is not None else None
    if bot is None:
        return
    for admin_id in ADMIN_IDS:
        for attempt in range(3):
            try:
                await bot.send_message(admin_id, message, reply_markup=reply_markup)
                break
            except Exception:
                if attempt == 2:
                    logger.exception('Could not notify admin %s', admin_id)
                else:
                    await asyncio.sleep(1.5 * (attempt + 1))

# ---------------- ADMIN DASHBOARD, ANALYTICS, AVAILABILITY, PRIVACY ----------------
def admin_dashboard_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📋 Booking Requests', callback_data='admin|requests'), InlineKeyboardButton('👥 Members', callback_data='admin|members')],



        [InlineKeyboardButton('📊 Analytics', callback_data='admin|analytics'), InlineKeyboardButton('🗓 Availability', callback_data='admin|availability')],
        [InlineKeyboardButton('🔔 Notifications', callback_data='admin|notifications'), InlineKeyboardButton('💾 Backup', callback_data='admin|backup')],
        [InlineKeyboardButton('🧾 Audit Log', callback_data='admin|audit'), InlineKeyboardButton('🩺 Health', callback_data='admin|health')],
    ])


async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    audit(update.effective_user.id, 'opened_admin_dashboard')
    await update.message.reply_text('🌸 Admin Panel — choose a section:', reply_markup=admin_dashboard_keyboard())


async def analytics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    conn = db()
    total = conn.execute('SELECT COUNT(*) n FROM members').fetchone()['n']
    interested = conn.execute("SELECT COUNT(*) n FROM members WHERE status IN ('interested','ready_to_confirm','booking_pending','booking_approved','booking_rejected','meet_later_financial','meet_later_outside_bangalore','interested_outside_city')").fetchone()['n']
    ready = conn.execute("SELECT COUNT(*) n FROM members WHERE status IN ('ready_to_confirm','booking_pending','booking_approved')").fetchone()['n']
    bookings = conn.execute('SELECT COUNT(*) n FROM booking_requests').fetchone()['n']
    approved = conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE status='approved'").fetchone()['n']
    completed = conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE status='completed'").fetchone()['n']
    week = conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE created_at >= datetime('now','-7 days')").fetchone()['n']
    month = conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE created_at >= datetime('now','-30 days')").fetchone()['n']
    conn.close()
    def pct(a,b): return f'{(100*a/b):.1f}%' if b else '—'
    await update.message.reply_text(
        '📊 Conversion Analytics\n\n'
        f'👥 Registered users: {total}\n❤️ Interested users: {interested} ({pct(interested,total)})\n'
        f'✅ Ready/booking users: {ready} ({pct(ready,total)})\n📥 Total requests: {bookings}\n'
        f'🟢 Approved: {approved} ({pct(approved,bookings)})\n🏁 Completed: {completed} ({pct(completed,bookings)})\n\n'
        f'📅 Requests in last 7 days: {week}\n🗓 Requests in last 30 days: {month}', reply_markup=admin_dashboard_keyboard())


async def addslot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    raw = update.message.text.partition(' ')[2].strip()
    if '|' not in raw: return await update.message.reply_text('Usage: /addslot 25 Oct 2026, 07:30 PM|2 hours')
    when, duration = [x.strip() for x in raw.split('|',1)]
    try: datetime.strptime(when, '%d %b %Y, %I:%M %p')
    except ValueError: return await update.message.reply_text('Use date format: 25 Oct 2026, 07:30 PM')
    conn = db()
    cur = conn.execute("INSERT INTO availability_slots(slot_datetime,duration,status) VALUES(?,?,'available')", (when,duration))
    slot_id = cur.lastrowid
    conn.commit(); conn.close()
    audit(update.effective_user.id, 'availability_slot_added', 'slot', slot_id, f'{when} | {duration}')
    await update.message.reply_text(f'✅ Added available slot #{slot_id}: {when} · {duration}')


async def availability_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    conn = db(); rows = conn.execute('SELECT * FROM availability_slots ORDER BY slot_datetime LIMIT 60').fetchall(); conn.close()
    if not rows: return await update.message.reply_text('No slots yet. Add one with /addslot 25 Oct 2026, 07:30 PM|2 hours')
    lines = ['🗓 Availability slots:']
    for r in rows: lines.append(f"#{r['id']} · {r['slot_datetime']} · {r['duration']} · {r['status']}")
    lines.append('\nAdd: /addslot 25 Oct 2026, 07:30 PM|2 hours\nRemove: /removeslot SLOT_ID')
    await update.message.reply_text('\n'.join(lines)[:3900], reply_markup=admin_dashboard_keyboard())


async def removeslot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    if not context.args or not context.args[0].isdigit(): return await update.message.reply_text('Usage: /removeslot SLOT_ID')
    slot_id = int(context.args[0]); conn = db()
    row = conn.execute('SELECT status FROM availability_slots WHERE id=?', (slot_id,)).fetchone()
    if not row: conn.close(); return await update.message.reply_text('Slot not found.')
    if row['status'] == 'booked': conn.close(); return await update.message.reply_text('This slot is booked; reject/cancel its booking before removing it.')
    conn.execute("UPDATE availability_slots SET status='removed' WHERE id=?", (slot_id,)); conn.commit(); conn.close()
    audit(update.effective_user.id, 'availability_slot_removed', 'slot', slot_id)
    await update.message.reply_text(f'Slot #{slot_id} removed.')


async def audit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    conn = db(); rows = conn.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT 30').fetchall(); conn.close()
    if not rows: return await update.message.reply_text('No audit events yet.')
    lines = ['🧾 Recent admin/bot activity:']
    for r in rows: lines.append(f"#{r['id']} {r['created_at']} actor={r['actor_id']} {r['action']} {r['target_type']}:{r['target_id']} {r['details']}")
    await update.message.reply_text('\n'.join(lines)[:3900], reply_markup=admin_dashboard_keyboard())


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    path = os.path.join(BACKUP_DIR, f'manual_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite3')
    src = sqlite3.connect(DB); dest = sqlite3.connect(path)
    src.backup(dest); dest.close(); src.close()
    try: os.chmod(path, 0o600)
    except OSError: pass
    audit(update.effective_user.id, 'manual_database_backup', 'file', os.path.basename(path))
    with open(path, 'rb') as f:
        await update.message.reply_document(document=f, filename=os.path.basename(path), caption='Database backup. Store securely; it contains member and booking data.')


async def restore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    context.user_data['awaiting_restore'] = True
    await update.message.reply_text('⚠️ Send a SQLite .db or .sqlite3 backup file as your next message. It will be validated before replacing the active database. A current backup will be created first. Use /cancelrestore to cancel.')


async def restore_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update) or not context.user_data.get('awaiting_restore'):
        return
    doc = update.message.document
    if not doc or not (doc.file_name or '').lower().endswith(('.db','.sqlite','.sqlite3')):
        return await update.message.reply_text('Please upload a .db, .sqlite, or .sqlite3 backup file.')
    context.user_data.pop('awaiting_restore', None)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix='.sqlite3'); os.close(fd)
    try:
        tgfile = await context.bot.get_file(doc.file_id); await tgfile.download_to_drive(tmp)
        test = sqlite3.connect(tmp)
        integrity = test.execute('PRAGMA integrity_check').fetchone()[0]
        tables = {r[0] for r in test.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        test.close()
        if integrity != 'ok' or 'members' not in tables or 'booking_requests' not in tables:
            return await update.message.reply_text('❌ This backup is invalid or missing required tables. Active database was not changed.')
        current = os.path.join(BACKUP_DIR, f'pre_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite3')
        src=sqlite3.connect(DB); dest=sqlite3.connect(current); src.backup(dest); dest.close(); src.close()
        # Replace DB after validation. Restart the service after restore for a clean connection state.
        for sidecar in (DB + '-wal', DB + '-shm'):
            try: os.remove(sidecar)
            except FileNotFoundError: pass
        shutil.copy2(tmp, DB)
        try: os.chmod(DB, 0o600)
        except OSError: pass
        audit(update.effective_user.id, 'database_restored', 'file', doc.file_name or 'backup')
        await update.message.reply_text('✅ Backup validated and restored. Please restart the Railway service now. The pre-restore database backup was retained.')
    except Exception:
        logger.exception('Database restore failed')
        await update.message.reply_text('❌ Restore failed; check Railway logs. Do not delete your existing backups.')
    finally:
        try: os.remove(tmp)
        except OSError: pass


async def cancelrestore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    context.user_data.pop('awaiting_restore', None)
    await update.message.reply_text('Restore cancelled.')


async def delete_my_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return
    await update.message.reply_text('⚠️ This permanently deletes your member profile and booking request records from this bot. Continue?', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🗑️ Yes, delete my data', callback_data='privacy|delete_confirm'), InlineKeyboardButton('Cancel', callback_data='back_main')]]))


async def perform_delete_my_data(user, context, query=None):
    conn = db()
    conn.execute("UPDATE availability_slots SET status='available',booked_request_id=NULL WHERE booked_request_id IN (SELECT id FROM booking_requests WHERE user_id=?)", (user.id,))
    conn.execute('DELETE FROM booking_requests WHERE user_id=?', (user.id,))
    conn.execute('DELETE FROM members WHERE user_id=?', (user.id,))
    conn.commit(); conn.close()
    audit(user.id, 'user_deleted_own_data', 'user', user.id)
    context.user_data.clear()
    msg = 'Your member profile and booking request records have been deleted from the bot database. This does not remove messages already delivered in Telegram chats.'
    if query:
        await query.edit_message_text(msg, reply_markup=main_menu())
    else:
        await context.bot.send_message(user.id, msg)


async def notifications_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    conn=db(); rows=conn.execute('SELECT category,enabled FROM notification_preferences ORDER BY category').fetchall(); conn.close()
    keys=[]
    for r in rows:
        state='ON' if r['enabled'] else 'OFF'
        keys.append([InlineKeyboardButton(f"{r['category'].title()} notifications: {state}", callback_data=f"notify|{r['category']}|{0 if r['enabled'] else 1}")])
    keys.append([InlineKeyboardButton('⬅️ Admin Panel', callback_data='admin|home')])
    await update.message.reply_text('🔔 Toggle admin notification categories:', reply_markup=InlineKeyboardMarkup(keys))


async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('Admin only.')
    try:
        conn=db(); integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
        members_n=conn.execute('SELECT COUNT(*) n FROM members').fetchone()['n']
        requests_n=conn.execute('SELECT COUNT(*) n FROM booking_requests').fetchone()['n']; conn.close()
        await update.message.reply_text(f'🩺 Health Check\nDatabase integrity: {integrity}\nMembers: {members_n}\nBooking requests: {requests_n}\nDatabase path configured: {bool(DB)}\nBackup directory: {BACKUP_DIR}')
    except Exception as exc:
        logger.exception('Health check failed')
        await update.message.reply_text(f'❌ Database health check failed: {type(exc).__name__}')


async def privacy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🔐 Privacy options\nUse /delete_my_data to delete your member profile and booking request records. Only admins can view member lists, booking requests, exports, and audit logs.')


async def advance_received_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command: /advance_received USER_ID after verifying receipt."""
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text('Usage: /advance_received USER_ID — use only after verifying the advance was received.')
    target_id = int(context.args[0])
    conn = db()
    row = conn.execute('SELECT user_id FROM members WHERE user_id=?', (target_id,)).fetchone()
    conn.close()
    if not row:
        return await update.message.reply_text('Member not found. They must start the bot first.')
    set_status(target_id, 'advance_received')
    audit(update.effective_user.id, 'advance_received_confirmed', 'member', target_id, 'Admin verified advance receipt; reminders stopped')
    try:
        await context.bot.send_message(target_id, '✅ Shruti has confirmed receipt of your advance. Daily availability reminders have stopped. For booking details or voice confirmation, contact @shruti23official.')
    except Exception:
        logger.info('Could not send advance-received confirmation to %s', target_id)
    await update.message.reply_text(f'✅ Advance marked received for user {target_id}. Daily reminders are now stopped.')


# ---------------- ADMIN COMMANDS ----------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    conn = db()
    total = conn.execute('SELECT COUNT(*) n FROM members').fetchone()['n']
    active = conn.execute('SELECT COUNT(*) n FROM members WHERE active=1').fetchone()['n']
    statuses = conn.execute('SELECT status,COUNT(*) n FROM members GROUP BY status').fetchall()
    requests = conn.execute('SELECT status,COUNT(*) n FROM booking_requests GROUP BY status').fetchall()
    conn.close()



    lines = ['📊 Admin Dashboard', f'👥 Registered members: {total}', f'🟢 Active members: {active}', '', 'Member statuses:']
    lines += [f'• {r["status"]}: {r["n"]}' for r in statuses]
    lines += ['', 'Booking requests:']
    lines += [f'• {r["status"]}: {r["n"]}' for r in requests] or ['• No booking requests yet']
    lines += ['', 'Use the buttons below or /dashboard for management tools.']
    await update.message.reply_text('\n'.join(lines), reply_markup=admin_dashboard_keyboard())


async def members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    conn = db()
    rows = conn.execute('SELECT user_id,first_name,last_name,username,status,active,updated_at FROM members ORDER BY updated_at DESC LIMIT 100').fetchall()
    conn.close()
    if not rows:
        return await update.message.reply_text('No members yet.')
    lines = ['👥 Latest members (max 100):']
    for r in rows:
        nm = ' '.join(x for x in [r['first_name'], r['last_name']] if x) or 'Unknown'
        lines.append(f"{nm} | @{r['username'] or 'none'} | ID {r['user_id']} | {r['status']} | active={r['active']} | {r['updated_at']}")
    text = '\n'.join(lines)
    for i in range(0, len(text), 3800):
        await update.message.reply_text(text[i:i+3800])


async def member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text('Usage: /member USER_ID')
    conn = db()
    row = conn.execute('SELECT * FROM members WHERE user_id=?', (int(context.args[0]),)).fetchone()
    requests = conn.execute('SELECT id,preferred_datetime,duration,location,status,created_at FROM booking_requests WHERE user_id=? ORDER BY id DESC LIMIT 10', (int(context.args[0]),)).fetchall()
    conn.close()
    if not row:
        return await update.message.reply_text('Member not found.')
    text = f"👤 {row['first_name']} {row['last_name']}\nUsername: @{row['username'] or 'none'}\nID: {row['user_id']}\nStatus: {row['status']}\nActive: {row['active']}\nRegistered: {row['created_at']}\nUpdated: {row['updated_at']}\n\nRecent booking requests:"
    for r in requests:
        text += f"\n#{r['id']} | {r['status']} | {r['preferred_datetime']} | {r['duration']} | {r['location']}"
    await update.message.reply_text(text[:3900])


async def interested_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    statuses = ['interested', 'meet_later_financial', 'meet_later_outside_bangalore',
                'interested_outside_city', 'ready_to_confirm', 'booking_pending', 'booking_approved']
    conn = db()
    placeholders = ','.join('?' for _ in statuses)
    rows = conn.execute(
        f"SELECT user_id,first_name,last_name,username,status,active FROM members WHERE status IN ({placeholders}) ORDER BY updated_at DESC",
        statuses,
    ).fetchall()
    conn.close()
    if not rows:
        return await update.message.reply_text('❤️ No interested members yet.')
    lines = ['❤️ Interested Members:']
    for r in rows:
        name = ' '.join(x for x in [r['first_name'], r['last_name']] if x) or 'Unknown'
        lines.append(f"{name} | @{r['username'] or 'none'} | ID {r['user_id']} | {r['status']} | active={r['active']}")
    text = '\n'.join(lines)
    for i in range(0, len(text), 3800):
        await update.message.reply_text(text[i:i+3800])


async def search_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    term = ' '.join(context.args).strip()
    if not term:
        return await update.message.reply_text('Usage: /search name_or_username_or_user_id')
    conn = db()
    like = f'%{term}%'
    rows = conn.execute('''SELECT user_id,first_name,last_name,username,status,active FROM members
        WHERE CAST(user_id AS TEXT) LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR username LIKE ?
        ORDER BY updated_at DESC LIMIT 30''', (like, like, like, like)).fetchall()
    conn.close()
    if not rows:
        return await update.message.reply_text('No matching members found.')
    lines = ['🔎 Search results:']
    for r in rows:
        nm = ' '.join(x for x in [r['first_name'], r['last_name']] if x) or 'Unknown'
        lines.append(f"{nm} | @{r['username'] or 'none'} | ID {r['user_id']} | {r['status']} | active={r['active']}")
    await update.message.reply_text('\n'.join(lines)[:3900])


async def booking_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    conn = db()
    rows = conn.execute("SELECT id,display_name,username,user_id,preferred_datetime,duration,location,status,created_at FROM booking_requests ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    if not rows:
        return await update.message.reply_text('No booking requests yet.')
    lines = ['📋 Recent booking requests:']
    for r in rows:
        lines.append(f"#{r['id']} | {r['status']} | {r['display_name']} (@{r['username'] or 'none'}) | ID {r['user_id']}\n{r['preferred_datetime']} · {r['duration']} · {r['location']}")
    text = '\n\n'.join(lines)
    for i in range(0, len(text), 3800):
        await update.message.reply_text(text[i:i+3800])


async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    conn = db()
    members_rows = conn.execute('SELECT * FROM members ORDER BY created_at DESC').fetchall()
    booking_rows = conn.execute('SELECT * FROM booking_requests ORDER BY id DESC').fetchall()
    conn.close()
    for label, rows in [('members.csv', members_rows), ('booking_requests.csv', booking_rows)]:
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        else:
            output.write('No records\n')
        bio = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        bio.name = label
        await update.message.reply_document(document=bio, filename=label)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    text = update.message.text.partition(' ')[2].strip()
    if not text:
        return await update.message.reply_text('Usage: /broadcast your message')
    context.user_data['broadcast_draft'] = {'text': text, 'target': 'all'}
    await update.message.reply_text(f'⚠️ Confirm broadcast to all active members?\n\n{text[:1000]}', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('✅ Send to all', callback_data='broadcast|confirm'), InlineKeyboardButton('Cancel', callback_data='broadcast|cancel')]]))


async def interested_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    text = update.message.text.partition(' ')[2].strip()
    if not text:
        return await update.message.reply_text('Usage: /interested your message')
    context.user_data['broadcast_draft'] = {'text': text, 'target': 'interested'}
    await update.message.reply_text(f'⚠️ Confirm broadcast to interested users?\n\n{text[:1000]}', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('✅ Send to interested', callback_data='broadcast|confirm'), InlineKeyboardButton('Cancel', callback_data='broadcast|cancel')]]))


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    context.user_data.pop('broadcast_draft', None)
    await update.message.reply_text('Broadcast cancelled.')


async def cancel_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await update.message.reply_text('Admin only.')
    context.user_data.pop('ask_details_request_id', None)
    await update.message.reply_text('Follow-up cancelled.')


async def admin_followup_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update) or not context.user_data.get('ask_details_request_id'):
        return False
    request_id = context.user_data.pop('ask_details_request_id')
    conn = db(); req = conn.execute('SELECT user_id FROM booking_requests WHERE id=?', (request_id,)).fetchone(); conn.close()
    if not req:
        await update.message.reply_text('Request not found.'); return True
    await context.bot.send_message(req['user_id'], f'📝 Admin has a follow-up question about booking request #{request_id}:\n\n{update.message.text}')
    await update.message.reply_text(f'Follow-up sent to user for request #{request_id}.')
    return True


async def all_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await admin_followup_text(update, context):
        return

    # Forward a user's optional message to Shruti after they choose Ready to Confirm.
    if context.user_data.get('awaiting_message_to_shruti') and update.effective_user:
        user = update.effective_user
        message_text = (update.effective_message.text or '').strip()
        if not message_text:
            return await update.effective_message.reply_text('Please type a text message, or tap Skip to continue.')
        if len(message_text) > 3000:
            return await update.effective_message.reply_text('Please keep your message under 3,000 characters and send it again.')
        context.user_data.pop('awaiting_message_to_shruti', None)
        admin_message = (
            '💌 Message for Shruti from a user\n\n'
            f'Name: {name_for(user)}\n'
            f'Username: @{user.username or "none"}\n'
            f'User ID: {user.id}\n\n'
            f'Message:\n{message_text}'
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
            await update.effective_message.reply_text(
                '❤️ Thank you! I’ve passed your message to Shruti.\n\n'
                'You can now send a booking request or contact her directly for booking and optional voice confirmation.',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('📝 Start booking request', callback_data='booking_start')],
                    [InlineKeyboardButton('💬 Contact @shruti23official', url='https://t.me/shruti23official')],
                    [InlineKeyboardButton('⬅️ Back to Menu', callback_data='back_main')],
                ]),
            )
        except Exception:
            logger.exception('Could not forward user message to Shruti')
            await update.effective_message.reply_text(
                'I could not deliver your message automatically. Please contact @shruti23official directly. ❤️',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('💬 Contact @shruti23official', url='https://t.me/shruti23official')]]),
            )
        return

    await handle_text(update, context)


async def notifications_cmd_from_query(query):
    conn=db(); rows=conn.execute('SELECT category,enabled FROM notification_preferences ORDER BY category').fetchall(); conn.close()
    keys=[[InlineKeyboardButton(f"{r['category'].title()} notifications: {'ON' if r['enabled'] else 'OFF'}", callback_data=f"notify|{r['category']}|{0 if r['enabled'] else 1}")] for r in rows]
    keys.append([InlineKeyboardButton('⬅️ Admin Panel', callback_data='admin|home')])
    return await query.edit_message_text('🔔 Toggle admin notification categories:', reply_markup=InlineKeyboardMarkup(keys))


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data or ''



    if data.startswith('privacy|'):
        query=update.callback_query; await query.answer()
        if data == 'privacy|delete_confirm':
            return await perform_delete_my_data(query.from_user, context, query)
    if data.startswith('admin|'):
        query=update.callback_query; await query.answer()
        if not is_admin(update): return await query.edit_message_text('Admin only.')
        action=data.split('|',1)[1]
        if action=='home': return await query.edit_message_text('🌸 Admin Panel', reply_markup=admin_dashboard_keyboard())
        if action=='requests':
            conn=db(); rows=conn.execute("SELECT id,display_name,preferred_datetime,duration,status FROM booking_requests WHERE status IN ('pending','needs_details') ORDER BY id DESC LIMIT 8").fetchall(); conn.close()
            if not rows: return await query.edit_message_text('📋 No pending booking requests.', reply_markup=admin_dashboard_keyboard())
            lines=['📋 Pending booking requests:']; keys=[]
            for r in rows:
                lines.append(f"#{r['id']} · {r['display_name']} · {r['preferred_datetime']} · {r['duration']} · {r['status']}")
                keys.append([InlineKeyboardButton(f"✅ Approve #{r['id']}", callback_data=f"req|approve|{r['id']}"), InlineKeyboardButton(f"❌ Reject #{r['id']}", callback_data=f"req|reject|{r['id']}")])
                keys.append([InlineKeyboardButton(f"📝 Ask for details #{r['id']}", callback_data=f"req|ask|{r['id']}")])
            keys.append([InlineKeyboardButton('⬅️ Admin Panel', callback_data='admin|home')])
            return await query.edit_message_text('\n'.join(lines)[:3500], reply_markup=InlineKeyboardMarkup(keys))
        if action=='members':
            conn=db(); rows=conn.execute('SELECT user_id,first_name,last_name,username,status FROM members ORDER BY updated_at DESC LIMIT 10').fetchall(); conn.close()
            text='👥 Recent members\n'+'\n'.join(f"{r['first_name']} {r['last_name']} · @{r['username'] or 'none'} · {r['status']} · ID {r['user_id']}" for r in rows) if rows else 'No members yet.'
            return await query.edit_message_text(text[:3500], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Use /search for more', callback_data='admin|home')],[InlineKeyboardButton('⬅️ Admin Panel', callback_data='admin|home')]]))
        if action=='analytics':
            conn=db(); total=conn.execute('SELECT COUNT(*) n FROM members').fetchone()['n']; reqs=conn.execute('SELECT COUNT(*) n FROM booking_requests').fetchone()['n']; approved=conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE status='approved'").fetchone()['n']; done=conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE status='completed'").fetchone()['n']; week=conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE created_at >= datetime('now','-7 days')").fetchone()['n']; month=conn.execute("SELECT COUNT(*) n FROM booking_requests WHERE created_at >= datetime('now','-30 days')").fetchone()['n']; conn.close()
            return await query.edit_message_text(f'📊 Analytics\nMembers: {total}\nRequests: {reqs}\nApproved: {approved}\nCompleted: {done}\nLast 7 days: {week}\nLast 30 days: {month}', reply_markup=admin_dashboard_keyboard())
        if action=='availability':
            conn=db(); rows=conn.execute('SELECT id,slot_datetime,duration,status FROM availability_slots ORDER BY slot_datetime LIMIT 20').fetchall(); conn.close()
            text='🗓 Availability\n'+'\n'.join(f"#{r['id']} {r['slot_datetime']} · {r['duration']} · {r['status']}" for r in rows) if rows else 'No slots configured. Use /addslot date, time|duration.'
            return await query.edit_message_text(text[:3900], reply_markup=admin_dashboard_keyboard())
        if action=='notifications':
            conn=db(); rows=conn.execute('SELECT category,enabled FROM notification_preferences ORDER BY category').fetchall(); conn.close()
            keys=[[InlineKeyboardButton(f"{r['category'].title()}: {'ON' if r['enabled'] else 'OFF'}", callback_data=f"notify|{r['category']}|{0 if r['enabled'] else 1}")] for r in rows]
            keys.append([InlineKeyboardButton('⬅️ Admin Panel', callback_data='admin|home')])
            return await query.edit_message_text('Toggle notification categories:', reply_markup=InlineKeyboardMarkup(keys))
        if action=='backup':
            return await query.edit_message_text('Use /backup to create and download a consistent database backup. Set BACKUP_DIR to a persistent Railway volume for automatic daily backups.', reply_markup=admin_dashboard_keyboard())
        if action=='audit':
            conn=db(); rows=conn.execute('SELECT created_at,actor_id,action,target_type,target_id FROM audit_log ORDER BY id DESC LIMIT 15').fetchall(); conn.close()
            text='🧾 Audit Log\n'+'\n'.join(f"{r['created_at']} · {r['actor_id']} · {r['action']} · {r['target_type']} {r['target_id']}" for r in rows) if rows else 'No audit events yet.'
            return await query.edit_message_text(text[:3900], reply_markup=admin_dashboard_keyboard())
        if action=='health':
            conn=db(); check=conn.execute('PRAGMA integrity_check').fetchone()[0]; members_n=conn.execute('SELECT COUNT(*) n FROM members').fetchone()['n']; req_n=conn.execute('SELECT COUNT(*) n FROM booking_requests').fetchone()['n']; conn.close()
            return await query.edit_message_text(f'🩺 Database: {check}\nMembers: {members_n}\nBooking requests: {req_n}', reply_markup=admin_dashboard_keyboard())
    if data.startswith('notify|'):
        query=update.callback_query; await query.answer()
        if not is_admin(update): return await query.edit_message_text('Admin only.')
        _, category, value=data.split('|',2)
        if category not in {'status','booking','errors','broadcast'} or value not in {'0','1'}: return await query.edit_message_text('Invalid setting.')
        conn=db(); conn.execute('UPDATE notification_preferences SET enabled=? WHERE category=?',(int(value),category)); conn.commit(); conn.close()
        audit(update.effective_user.id,'notification_preference_changed','setting',category,value)
        return await notifications_cmd_from_query(query)
    if data.startswith('broadcast|'):
        query = update.callback_query; await query.answer()
        if not is_admin(update):
            return await query.edit_message_text('Admin only.')
        if data.endswith('cancel'):
            context.user_data.pop('broadcast_draft', None)
            return await query.edit_message_text('Broadcast cancelled.')
        draft = context.user_data.pop('broadcast_draft', None)
        if not draft:
            return await query.edit_message_text('No broadcast draft found.')
        if draft['target'] == 'all':
            targets = get_users()
        else:
            conn = db(); statuses = ['interested','meet_later_financial','meet_later_outside_bangalore','interested_outside_city','ready_to_confirm','booking_pending','booking_approved']
            placeholders = ','.join('?' for _ in statuses)
            targets = [r['user_id'] for r in conn.execute(f'SELECT user_id FROM members WHERE active=1 AND status IN ({placeholders})', statuses).fetchall()]
            conn.close()
        sent = failed = 0
        for uid in targets:
            delivered = False
            for attempt in range(2):
                try:
                    await context.bot.send_message(uid, draft['text'])
                    sent += 1; delivered = True; break
                except Exception:
                    if attempt == 0:
                        await asyncio.sleep(0.4)
                    else:
                        failed += 1
        audit(update.effective_user.id, 'broadcast_completed', 'broadcast', draft['target'], f'sent={sent}; failed={failed}')
        await notify_admin(context, f'📢 Broadcast completed. Target: {draft["target"]}; sent={sent}; failed={failed}.', category='broadcast')
        return await query.edit_message_text(f'📢 Broadcast complete.\nSent: {sent}\nFailed: {failed}')
    return await buttons(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Unhandled exception while processing update', exc_info=context.error)
    try:
        alert_errors = pref_enabled('errors')
    except Exception:
        alert_errors = False
    if alert_errors:
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, f'⚠️ Bot error occurred: {type(context.error).__name__}. Check Railway logs for details.')
            except Exception:
                logger.exception('Could not send error alert to admin')


# ---------------- APPLICATION ----------------
def main():
    db().close()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('status', status_cmd))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('admin', stats))
    app.add_handler(CommandHandler('members', members))
    app.add_handler(CommandHandler('member', member))
    app.add_handler(CommandHandler('search', search_members))
    app.add_handler(CommandHandler('interestedlist', interested_list))
    app.add_handler(CommandHandler('requests', booking_requests))
    app.add_handler(CommandHandler('export', export_csv))
    app.add_handler(CommandHandler('broadcast', broadcast))
    app.add_handler(CommandHandler('interested', interested_broadcast))
    app.add_handler(CommandHandler('cancelbroadcast', cancel_broadcast))
    app.add_handler(CommandHandler('cancelask', cancel_ask))
    app.add_handler(CommandHandler('dashboard', dashboard_cmd))
    app.add_handler(CommandHandler('analytics', analytics_cmd))
    app.add_handler(CommandHandler('addslot', addslot_cmd))
    app.add_handler(CommandHandler('availability', availability_cmd))
    app.add_handler(CommandHandler('removeslot', removeslot_cmd))
    app.add_handler(CommandHandler('audit', audit_cmd))
    app.add_handler(CommandHandler('backup', backup_cmd))
    app.add_handler(CommandHandler('restore', restore_cmd))
    app.add_handler(CommandHandler('cancelrestore', cancelrestore_cmd))
    app.add_handler(CommandHandler('delete_my_data', delete_my_data))
    app.add_handler(CommandHandler('privacy', privacy_cmd))
    app.add_handler(CommandHandler('notifications', notifications_cmd))
    app.add_handler(CommandHandler('health', health_cmd))
    app.add_handler(CommandHandler('advance_received', advance_received_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, restore_document))
    app.add_handler(CallbackQueryHandler(button_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_router))
    app.add_error_handler(error_handler)
    logger.info('Bot starting; CHANNEL_ID configured=%s; daily group posting configured=%s', bool(CHANNEL_ID), bool(GROUP_IDS))
    app.run_polling()

if __name__ == '__main__':
    main()








        


        

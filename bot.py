# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import asyncio

# ========================
# CONFIG
# ========================

TOKEN = "8511247299:AAHHnAdWUv8LPFxxExYgyLKCmhENB4947pU"

LATE_FINE = 500

# ========================
# STAFF SHIFT SETTINGS (USERNAME BASED)
# ========================

STAFF_SHIFTS = {

    "saji": {
        "name": "Saji",
        "start_hour": 13,
        "start_minute": 0,
        "end_hour": 2,
        "end_minute": 0
    },

    "sajawal": {
        "name": "Sajawal",
        "start_hour": 13,
        "start_minute": 0,
        "end_hour": 2,
        "end_minute": 0
    },

    "daniyal": {
        "name": "Daniyal",
        "start_hour": 13,
        "start_minute": 0,
        "end_hour": 2,
        "end_minute": 0
    }
}

# ========================
# STORAGE
# ========================

active_breaks = {}
work_sessions = {}
smoke_breaks = {}
wc_breaks = {}

# ========================
# HELPERS
# ========================

def now():
    return datetime.now()

def format_time(dt=None):
    return (dt or now()).strftime("%d-%m-%Y %I:%M:%S %p")

def format_minutes(m):
    return f"{m//60}h {m%60}m"

async def send(update: Update, text: str):
    await update.message.reply_text(text)

def get_username(update: Update):
    username = update.effective_user.username
    if not username:
        return None
    return username.lower()

def is_on_break(uid):
    return uid in active_breaks

# ========================
# BREAK REMINDER
# ========================

async def break_reminder(context, uid):

    alerted = False

    while uid in active_breaks:

        await asyncio.sleep(60)

        if uid not in active_breaks:
            return

        data = active_breaks[uid]

        elapsed = int((now() - data["start"]).seconds // 60)

        if elapsed > data["allowed"] and not alerted:

            late = elapsed - data["allowed"]

            await context.bot.send_message(
                chat_id=data["chat_id"],
                text=f"""
⚠ OVER TIME ALERT

👤 {data['name']}
📌 {data['type']}
⏰ Late {late} min
💸 Fine PKR {LATE_FINE}

Use /back immediately!
"""
            )

            alerted = True

# ========================
# START WORK
# ========================

async def startwork(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    if not uid:
        return await send(update, "❌ Please set a Telegram username first.")

    if uid not in STAFF_SHIFTS:
        return await send(update, "❌ You are not registered for duty.")

    if uid in work_sessions:
        return await send(update, "❌ Work already started.")

    shift = STAFF_SHIFTS[uid]
    current = now()

    shift_start = current.replace(
        hour=shift["start_hour"],
        minute=shift["start_minute"],
        second=0,
        microsecond=0
    )

    late_minutes = 0
    fine = 0

    if current > shift_start:
        late_minutes = int((current - shift_start).seconds // 60)
        fine = LATE_FINE

    work_sessions[uid] = {
        "name": shift["name"],
        "start": current,
        "total_break": 0,
        "total_fine": fine
    }

    await send(update, f"""
━━━━━━━━━━━━━━━━━━
✅ WORK STARTED
━━━━━━━━━━━━━━━━━━

👤 {shift['name']}

🕒 Start Time
➜ {format_time(current)}

⏰ Shift Time
➜ 01:00 PM → 02:00 AM

⏰ Late
➜ {late_minutes} min

💸 Fine
➜ PKR {fine}

━━━━━━━━━━━━━━━━━━
""")

# ========================
# END WORK
# ========================

async def endwork(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    if uid not in work_sessions:
        return await send(update, "❌ No active session.")

    if is_on_break(uid):
        return await send(update, "❌ Use /back first.")

    data = work_sessions[uid]

    total_minutes = int((now() - data["start"]).seconds // 60)

    break_minutes = data["total_break"]

    actual = max(0, total_minutes - break_minutes)

    smoke = smoke_breaks.get(uid, 0)
    wc = wc_breaks.get(uid, 0)

    await send(update, f"""
━━━━━━━━━━━━━━━━━━
🛑 SHIFT END
━━━━━━━━━━━━━━━━━━

👤 {data['name']}

🕒 Total Time
➜ {format_minutes(total_minutes)}

💼 Work Time
➜ {format_minutes(actual)}

☕ Breaks
➜ {format_minutes(break_minutes)}

🚬 Smoke
➜ {smoke}/5

🚻 WC
➜ {wc}/5

💸 Fine
➜ PKR {data['total_fine']}

━━━━━━━━━━━━━━━━━━
""")

    del work_sessions[uid]

# ========================
# BREAK SYSTEM
# ========================

def start_break(uid, name, chat_id, btype, allowed):

    active_breaks[uid] = {
        "type": btype,
        "start": now(),
        "allowed": allowed,
        "chat_id": chat_id,
        "name": name
    }

# ========================
# BREAK COMMANDS
# ========================

async def breakfast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    if is_on_break(uid):
        return await send(update, "❌ Already on break.")

    start_break(uid, uid, update.effective_chat.id, "Breakfast", 45)

    await send(update, f"🍳 Breakfast Started\n🕒 {format_time()}")

    asyncio.create_task(break_reminder(context, uid))

async def lunch(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    if is_on_break(uid):
        return await send(update, "❌ Already on break.")

    start_break(uid, uid, update.effective_chat.id, "Lunch", 45)

    await send(update, f"🍔 Lunch Started\n🕒 {format_time()}")

    asyncio.create_task(break_reminder(context, uid))

async def dinner(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    if is_on_break(uid):
        return await send(update, "❌ Already on break.")

    start_break(uid, uid, update.effective_chat.id, "Dinner", 30)

    await send(update, f"🍽 Dinner Started\n🕒 {format_time()}")

    asyncio.create_task(break_reminder(context, uid))

async def smokebreak(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    smoke_breaks[uid] = smoke_breaks.get(uid, 0)

    if smoke_breaks[uid] >= 5:
        return await send(update, "❌ Smoke limit reached.")

    smoke_breaks[uid] += 1

    start_break(uid, uid, update.effective_chat.id, "Smoke", 10)

    await send(update, f"🚬 Smoke Break {smoke_breaks[uid]}/5")

    asyncio.create_task(break_reminder(context, uid))

async def wcbreak(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    wc_breaks[uid] = wc_breaks.get(uid, 0)

    if wc_breaks[uid] >= 5:
        return await send(update, "❌ WC limit reached.")

    wc_breaks[uid] += 1

    start_break(uid, uid, update.effective_chat.id, "WC", 20)

    await send(update, f"🚻 WC Break {wc_breaks[uid]}/5")

    asyncio.create_task(break_reminder(context, uid))

# ========================
# BACK
# ========================

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = get_username(update)

    if uid not in active_breaks:
        return await send(update, "❌ No active break.")

    data = active_breaks[uid]

    duration = int((now() - data["start"]).seconds // 60)

    late = max(0, duration - data["allowed"])

    fine = LATE_FINE if late > 0 else 0

    if uid in work_sessions:
        work_sessions[uid]["total_break"] += duration
        work_sessions[uid]["total_fine"] += fine

    await send(update, f"""
✅ BACK TO WORK

📌 {data['type']}
⏱ {duration} min
⚠ Late {late} min
💸 Fine {fine}
""")

    del active_breaks[uid]

# ========================
# APP
# ========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("startwork", startwork))
app.add_handler(CommandHandler("endwork", endwork))

app.add_handler(CommandHandler("breakfast", breakfast))
app.add_handler(CommandHandler("lunch", lunch))
app.add_handler(CommandHandler("dinner", dinner))

app.add_handler(CommandHandler("smokebreak", smokebreak))
app.add_handler(CommandHandler("wcbreak", wcbreak))

app.add_handler(CommandHandler("back", back))

print("Bot is running...")

app.run_polling()
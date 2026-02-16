import os
import sqlite3
import threading
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ============================
# CONFIGURACIÓN
# ============================

TOKEN = "8396145802:AAEpRmDYBzuwzZL3Bxgc52bvkHemi-3yc6w"

ADMINS = [
    6425859947,
    8374336790,
    1518190436,
    8316910199
]

CHANNEL_ID = -1003530748898
GROUP_ID = -1000000000000

# ============================
# BASE DE DATOS
# ============================

conn = sqlite3.connect("confesiones.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS confesiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    content_type TEXT,
    message_id INTEGER,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS rate_limit (
    user_id INTEGER,
    date TEXT,
    count INTEGER,
    PRIMARY KEY (user_id, date)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    confession_id INTEGER,
    admin_id INTEGER,
    action TEXT,
    timestamp TEXT
)
""")

conn.commit()

# ============================
# FUNCIÓN PARA VERIFICAR ADMIN
# ============================

def is_admin(user_id):
    return user_id in ADMINS

# ============================
# RATE LIMIT
# ============================

def check_rate_limit(user_id):
    if user_id in ADMINS:
        return True

    today = time.strftime("%Y-%m-%d")

    cursor.execute("SELECT count FROM rate_limit WHERE user_id=? AND date=?", (user_id, today))
    row = cursor.fetchone()

    if row:
        if row[0] >= 10:
            return False
        cursor.execute("UPDATE rate_limit SET count=count+1 WHERE user_id=? AND date=?", (user_id, today))
    else:
        cursor.execute("INSERT INTO rate_limit (user_id, date, count) VALUES (?, ?, 1)", (user_id, today))

    conn.commit()
    return True

# ============================
# KEEP ALIVE
# ============================

def keep_alive_thread(bot):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def ping():
        try:
            await bot.get_me()
            print("✅ Keep-alive enviado")
        except Exception as e:
            print(f"⚠️ Error en keep-alive: {e}")

    while True:
        loop.run_until_complete(ping())
        time.sleep(120)

# ============================
# MENSAJE AUTOMÁTICO AL INICIAR
# ============================

def startup_message_thread(bot):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def send_start():
        for admin in ADMINS:
            try:
                await bot.send_message(
                    chat_id=admin,
                    text="✅ El bot se inició correctamente.\n📨 Esperando confesiones..."
                )
                print(f"Mensaje de inicio enviado a {admin}")
            except Exception as e:
                print(f"⚠️ Error enviando mensaje de inicio a {admin}: {e}")

    loop.run_until_complete(send_start())

# ============================
# COMANDO /start
# ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    user_keyboard = [["📝 Hacer una confesión"]]

    admin_keyboard = [
        ["📌 Pendientes", "📊 Estadísticas"],
        ["📜 Logs"],
        ["📝 Hacer una confesión"]
    ]

    keyboard = admin_keyboard if user_id in ADMINS else user_keyboard

    await update.message.reply_text(
        "Envía tu confesión de forma anónima ✅\n"
        "Puedes enviar texto, fotos, videos, audios o documentos.\n\n"
        "Presiona un botón para comenzar:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ============================
# FUNCIÓN /test PARA DIAGNÓSTICO
# ============================

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Probando envío a admins... revisa la consola.")

    for admin in ADMINS:
        try:
            await context.bot.send_message(admin, "🔧 Test directo del bot")
            print(f"OK → Mensaje enviado a {admin}")
        except Exception as e:
            print(f"ERROR → No puedo enviarle a {admin}: {e}")

# ============================
# MANEJO DE BOTONES PERSISTENTES
# ============================

async def handle_persistent_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "📝 Hacer una confesión":
        await update.message.reply_text("✅ Envía tu confesión ahora.")
        return

    if user_id in ADMINS:

        if text == "📌 Pendientes":
            cursor.execute("SELECT COUNT(*) FROM confesiones WHERE status='pending'")
            count = cursor.fetchone()[0]
            await update.message.reply_text(f"📌 Confesiones pendientes: {count}")
            return

        if text == "📊 Estadísticas":
            cursor.execute("SELECT COUNT(*) FROM confesiones")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM confesiones WHERE status='approved'")
            approved = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM confesiones WHERE status='rejected'")
            rejected = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM confesiones WHERE status='pending'")
            pending = cursor.fetchone()[0]

            await update.message.reply_text(
                f"📊 *Estadísticas*\n"
                f"Total: {total}\n"
                f"Aprobadas: {approved}\n"
                f"Rechazadas: {rejected}\n"
                f"Pendientes: {pending}",
                parse_mode="Markdown"
            )
            return

        if text == "📜 Logs":
            cursor.execute("""
                SELECT confession_id, admin_id, action, timestamp
                FROM logs ORDER BY id DESC LIMIT 20
            """)
            rows = cursor.fetchall()

            if not rows:
                await update.message.reply_text("📜 No hay logs todavía.")
                return

            msg = "📜 *Últimos 20 logs:*\n\n"
            for c_id, admin, action, ts in rows:
                msg += f"• Confesión #{c_id} — {action.upper()} por {admin} — {ts}\n"

            await update.message.reply_text(msg, parse_mode="Markdown")
            return

# ============================
# RECIBIR CONFESIÓN
# ============================

async def receive_confession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    user = update.message.from_user
    message = update.message

    print("CONFESIÓN RECIBIDA:", user.id)

    if not check_rate_limit(user.id):
        await message.reply_text("⛔ Has alcanzado el límite de 10 confesiones por día.")
        return

    last_time = context.user_data.get("last_confession")
    if last_time:
        if (message.date - last_time).total_seconds() < 10:
            await message.reply_text("⏳ Espera unos segundos antes de enviar otra confesión.")
            return

    context.user_data["last_confession"] = message.date

    if message.text:
        content_type = "text"
    elif message.photo:
        content_type = "photo"
    elif message.video:
        content_type = "video"
    elif message.audio:
        content_type = "audio"
    elif message.voice:
        content_type = "voice"
    elif message.document:
        content_type = "document"
    else:
        content_type = "other"

    cursor.execute("""
        INSERT INTO confesiones (user_id, username, content_type, message_id, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user.id,
        user.first_name or "",
        content_type,
        message.message_id,
        "pending"
    ))
    conn.commit()

    confession_id = cursor.lastrowid

    keyboard = [
        [
            InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{confession_id}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{confession_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin in ADMINS:
        print("Intentando enviar a admin:", admin)
        try:
            await context.bot.send_message(
                chat_id=admin,
                text=f"📩 Nueva confesión #{confession_id}\nDe: {user.first_name} (ID: {user.id})\nTipo: {content_type}"
            )
            await message.copy(chat_id=admin, reply_markup=reply_markup)
        except Exception as e:
            print(f"ERROR enviando a admin {admin}: {e}")

    await message.reply_text("✅ Tu confesión fue enviada para revisión.")

# ============================
# BOTONES DE APROBAR / RECHAZAR
# ============================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, confession_id = query.data.split("_")
    confession_id = int(confession_id)

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ No tienes permiso para hacer esto.")
        return

    cursor.execute("SELECT message_id, user_id, status FROM confesiones WHERE id=?", (confession_id,))
    row = cursor.fetchone()

    if not row:
        await query.edit_message_text("❌ Esta confesión ya no existe.")
        return

    original_message_id, user_id, status = row

    if status != "pending":
        await query.edit_message_text("⚠️ Esta confesión ya fue revisada por otro administrador.")
        return

    cursor.execute("""
        INSERT INTO logs (confession_id, admin_id, action, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        confession_id,
        query.from_user.id,
        action,
        time.strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()

    if action == "approve":
        try:
            sent = await context.bot.copy_message(
                chat_id=CHANNEL_ID,
                from_chat_id=user_id,
                message_id=original_message_id
            )

            try:
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"💬 Comentarios para confesión #{confession_id}",
                    reply_to_message_id=sent.message_id
                )
            except:
                pass

        except Exception as e:
            await query.edit_message_text(f"❌ Error al publicar en el canal:\n{e}")
            return

        cursor.execute("UPDATE confesiones SET status='approved' WHERE id=?", (confession_id,))
        conn.commit()

        await query.edit_message_text(f"✅ Confesión aprobada por {query.from_user.first_name}.")

        try:
            await context.bot.send_message(user_id, "✅ Tu confesión fue aprobada.")
        except:
            pass

    else:
        cursor.execute("UPDATE confesiones SET status='rejected' WHERE id=?", (confession_id,))
        conn.commit()

        await query.edit_message_text(f"❌ Confesión rechazada por {query.from_user.first_name}.")

        try:
            await context.bot.send_message(user_id, "❌ Tu confesión fue rechazada.")
        except:
            pass

    for admin in ADMINS:
        if admin != query.from_user.id:
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=admin,
                    message_id=query.message.message_id,
                    reply_markup=None
                )
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"⚠️ La confesión #{confession_id} ya fue revisada por {query.from_user.first_name}."
                )
            except:
                pass

# ============================
# INICIO DEL BOT (CORREGIDO)
# ============================

async def post_init(app):
    threading.Thread(target=keep_alive_thread, args=(app.bot,), daemon=True).start()
    threading.Thread(target=startup_message_thread, args=(app.bot,), daemon=True).start()

def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))

    app.add_handler(
        MessageHandler(
            filters.Regex("^(📝 Hacer una confesión|📌 Pendientes|📊 Estadísticas|📜 Logs)$"),
            handle_persistent_buttons
        )
    )

    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, receive_confession)
    )

    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot de confesiones iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()








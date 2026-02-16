from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import os
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 6425859947 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot funcionando ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    
    await update.message.reply_text(f"escribiste : {text}")


    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Nuevo mensaje:\nDe: {user.first_name} (ID: {user.id})\nMensaje: {text}"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

print("Bot iniciado ✅")
app.run_polling()


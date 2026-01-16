import os
from fastapi import FastAPI, Request
import uvicorn

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from evaluator import evaluate_hardware


# =========================
# KONFIGURACJA
# =========================

TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", 8080))


# =========================
# BOT TELEGRAM
# =========================

application = ApplicationBuilder().token(TOKEN).build()


MAIN_MENU = (
    "📋 *Menu główne*\n\n"
    "1️⃣ Sprawdź specyfikację komputera\n"
    "2️⃣ Jak sprawdzić wymagania?\n"
    "3️⃣ Specyficzne przypadki"
)

CHECK_PROMPT = "Podaj CPU i RAM, np. `i5-8250U, 8GB RAM`"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = evaluate_hardware(update.message.text)
    await update.message.reply_text(result)


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# =========================
# FASTAPI WEBHOOK
# =========================

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")


@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


# =========================
# START SERWERA
# =========================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)

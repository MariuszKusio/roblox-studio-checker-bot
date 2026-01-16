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
    text = update.message.text.strip()

    # =========================
    # MENU GŁÓWNE (NAJPIERW!)
    # =========================

    if text == "1":
        context.user_data["mode"] = "check_hardware"
        await update.message.reply_text(CHECK_PROMPT, parse_mode="Markdown")
        return

    if text == "2":
        context.user_data["mode"] = "choose_os"
        await update.message.reply_text(OS_MENU, parse_mode="Markdown")
        return

    if text == "3":
        await update.message.reply_text(SPECIFIC_INFO, parse_mode="Markdown")
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    # =========================
    # TRYBY (DOPIERO TERAZ)
    # =========================

    mode = context.user_data.get("mode")

    if mode == "check_hardware":
        result = evaluate_hardware(text)
        context.user_data.clear()
        await update.message.reply_text(result)
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    if mode == "choose_os":
        if text == "1":
            await update.message.reply_text(
                "🪟 *Windows*\n\nRoblox Studio działa na Windows 10 i 11.",
                parse_mode="Markdown",
            )
        elif text == "2":
            await update.message.reply_text(
                "🍎 *macOS*\n\nRoblox Studio działa na macOS (Intel / Apple Silicon).",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("❌ Wybierz 1 lub 2.")
            return

        context.user_data.clear()
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    # =========================
    # NIEZNANE
    # =========================

    await update.message.reply_text(
        "❓ Nie rozumiem.\nWpisz /menu, aby zobaczyć opcje.",
        parse_mode="Markdown",
    )


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

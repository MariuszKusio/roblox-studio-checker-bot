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
    "1️⃣ Sprawdź specyfikację komputera pod RobloxStudio\n"
    "2️⃣ Jak sprawdzić wymagania?\n"
    "3️⃣ Specyficzne przypadki (chromeOS,tablet itd.)"
)

CHECK_PROMPT = "Podaj CPU i RAM w formacie - `i5-8250U, 8GB RAM`"

OS_MENU = (
    "💻 *Wybierz system operacyjny:*\n\n"
    "1️⃣ Windows\n"
    "2️⃣ macOS"
)

SPECIFIC_INFO = (
    "ℹ️ *Specyficzne przypadki:*\n\n"
    "• Tablety nie nadają się do pracy w Roblox Studio\n"
    "• Komputery z ChromeOS nie obsługują Roblox Studio\n"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    # =========================
    # TRYB: JAK SPRAWDZIĆ WYMAGANIA (PODMENU OS)
    # =========================

    if mode == "choose_os":
        if text == "1":
            await update.message.reply_text(
                "🪟 *Windows – jak sprawdzić specyfikację*\n\n"
                "Sposób dokładny\n"
                "1. Kliknij w ikonke windowsa - zazwyczaj lewy dolny róg\n"
                "2. Wybierz *Ustawienia - ikonka koła zębatego*\n"
                "3. Wybierz *System*\n"
                "4. Po lewej stronie okna zjedź na sam dół listy i wybierz - informacje\n"
                "5. Pojawi się informacja o Procesorze i Pamięci RAM \n\n"
                "Sposób szybki - mniej dokłady\n"
                "1. Skrót kalwiszowy windows+R\n"
                "2. Wpisz msinfo32 -> enter\n"
                "3. Dostęp do modelu procesora\n\n"
                "Sposób gdy mamy drugi laptop - bez uruchomienia (laptop)\n"
                "1. Sprawdzenie dokładnego modelu laptopa - zazwyczaj najlepka z tyłu \n"
                "2. Wyszukaj specyfikacje konkretnego modelu w google\n"
                ,
                parse_mode="Markdown",
            )

        elif text == "2":
            await update.message.reply_text(
                "🍎 *macOS – jak sprawdzić specyfikację*\n\n"
                "1. Kliknij w logo Apple \n"
                "2. Wybierz *Ten Mac*\n"
                "3. Sprawdź:\n"
                "   • Chip / Procesor\n"
                "   • Pamięć (RAM)\n\n"
                "Przykład do wpisania:\n"
                "`M1, 8GB RAM`",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("❌ Wybierz 1 lub 2.")
            return

        context.user_data.clear()
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    # =========================
    # TRYB: OCENA SPRZĘTU
    # =========================

    if mode == "check_hardware":
        result = evaluate_hardware(text)
        context.user_data.clear()
        await update.message.reply_text(result)
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    # =========================
    # MENU GŁÓWNE
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

import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from evaluator import evaluate_hardware

TOKEN = os.environ.get("TELEGRAM_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

# =========================
# MENU TEKSTY
# =========================

MAIN_MENU = (
    "📋 *Menu główne*\n\n"
    "Wpisz numer wybranej pozycji:\n\n"
    "1️⃣ Sprawdź specyfikację komputera pod Roblox Studio\n"
    "2️⃣ Jak dokładnie sprawdzić wymagania?\n"
    "3️⃣ Specyficzne przypadki (macOS, ChromeOS)"
)

HELP_TEXT = (
    "🤖 *Pomoc*\n\n"
    "Dostępne komendy:\n"
    "• /start – uruchom bota\n"
    "• /menu – pokaż menu główne\n\n"
    "Jak korzystać:\n"
    "1️⃣ Wpisz /menu\n"
    "2️⃣ Wybierz numer opcji\n"
    "3️⃣ Postępuj zgodnie z instrukcjami\n"
)

CHECK_PROMPT = (
    "🖥️ *Sprawdzanie sprzętu*\n\n"
    "Wprowadź dokładny model procesora oraz ilość pamięci RAM.\n"
    "Przykład:\n"
    "`i5-10400F, 8GB RAM`"
)

OS_MENU = (
    "💻 *Wybierz system operacyjny:*\n\n"
    "1️⃣ Windows\n"
    "2️⃣ macOS"
)

SPECIFIC_INFO = (
    "ℹ️ *Specyficzne przypadki:*\n\n"
    "• Tablety nie mogą być wykorzystywane do pracy w Roblox Studio\n"
    "• Komputery z ChromeOS nie obsługują Roblox Studio\n"
    "• Roblox Studio wymaga klasycznego systemu desktopowego\n"
)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        MAIN_MENU,
        parse_mode="Markdown"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        MAIN_MENU,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown") 


# =========================
# GŁÓWNY HANDLER
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Sprawdź aktualny tryb użytkownika
    mode = context.user_data.get("mode")

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))

    # -------------------------
    # TRYB: OCENA SPRZĘTU
    # -------------------------
    if mode == "check_hardware":
        result = evaluate_hardware(text)
        context.user_data.clear()
        await update.message.reply_text(result)
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    # -------------------------
    # TRYB: WYBÓR OS
    # -------------------------
    if mode == "choose_os":
        if text == "1":
            await update.message.reply_text(
                "🪟 *Windows*\n\n"
                "Roblox Studio działa poprawnie na Windows 10 i 11.\n"
                "Zalecane są aktualne sterowniki graficzne.",
                parse_mode="Markdown"
            )
        elif text == "2":
            await update.message.reply_text(
                "🍎 *macOS*\n\n"
                "Roblox Studio działa tylko na komputerach Mac\n"
                "z procesorami Intel lub Apple Silicon.\n"
                "Starsze Maci mogą mieć ograniczoną wydajność.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Wybierz 1 lub 2.")
            return

        context.user_data.clear()
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    # -------------------------
    # MENU GŁÓWNE
    # -------------------------
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

    # -------------------------
    # NIEZNANE
    # -------------------------
    await update.message.reply_text(
         "❓ Nie rozumiem tej komendy.\n\n"
    "Wpisz /start, aby zobaczyć dostępne opcje.",
    parse_mode="Markdown"
    )


# =========================
# APP
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot uruchomiony...")
# app.run_polling()

import os
from telegram.ext import Application

PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if __name__ == "__main__":
    application = app

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

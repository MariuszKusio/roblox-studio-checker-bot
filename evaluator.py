import re
import os
import requests
from datetime import datetime

# ==================================================
# BEZWZGLĘDNIE ODRZUCANE – WSZYSTKIE 2-RDZENIOWE CPU
# ==================================================

DUAL_CORE_CPUS = {
    # Intel i3 (2C)
    "i3-6100u", "i3-7100u", "i3-8130u", "i3-8145u",
    "i3-1005g1", "i3-10110u", "i3-1115g4",

    # Intel i5 (2C)
    "i5-4200u", "i5-4300u",
    "i5-5200u", "i5-5300u",
    "i5-6200u", "i5-6300u",
    "i5-7200u", "i5-7300u",

    # Intel i7 (2C)
    "i7-6500u", "i7-6600u",
    "i7-7500u", "i7-7600u",

    # Intel Y-series
    "i5-8200y", "i5-8210y",
    "i7-8500y", "i7-8600y",

    # AMD Ryzen 2C
    "ryzen32200u",
    "ryzen32300u",
    "ryzenr1505g",
    "ryzenr1606g",
}

# ==================================================
# TWARDY WYJĄTEK – INTEL N (BEZ DALSZEJ LOGIKI)
# ==================================================

INTEL_N_FORCE_OK = {
    "intel n95",
    "intel n100",
    "intel n150",
    "intel n200",
    "intel n250",
    "intel n305",
    "intel i3-n305",
    "intel n350",
    "intel n355",
    "Intel Core i3-N305",
    "intel processor n100",
    "intel processor n150",
    "intel processor n200",
    "intel processor n250",
    "intel processor n305",
}

# ==================================================
# SPECJALNE MODELE (ZNANE, OK)
# ==================================================

INTEL_SPECIAL_OK = {
    "pentiumgold8505",
    "n95", "n350", "n355",
}

GSHEET_WEBHOOK_URL = os.environ.get("GSHEET_WEBHOOK_URL")

# ==================================================
# POMOCNICZE
# ==================================================

def normalize(text: str) -> str:
    return text.lower().replace(" ", "")

def extract_ram_gb(text: str):
    m = re.search(r"(\d+)\s*gb", text.lower())
    return int(m.group(1)) if m else None

def extract_intel_model(cpu: str):
    m = re.search(r"(i[3579]-\d{4,5}[a-z]*)", cpu.lower())
    return m.group(1) if m else None

def extract_intel_generation(model: str):
    m = re.search(r"i[3579]-(\d{4,5})", model)
    if not m:
        return None
    num = m.group(1)
    return int(num[:2]) if len(num) == 5 else int(num[0])

# ==================================================
# GOOGLE SHEETS – LOG NIEZNANYCH
# ==================================================

def log_unknown_cpu(cpu: str, ram: int):
    if not GSHEET_WEBHOOK_URL:
        return
    try:
        requests.post(
            GSHEET_WEBHOOK_URL,
            json={
                "cpu": cpu,
                "ram": ram,
                "date": datetime.utcnow().isoformat()
            },
            timeout=5
        )
    except Exception:
        pass

# ==================================================
# GŁÓWNA OCENA CPU
# ==================================================

def evaluate_cpu(cpu_name: str) -> str:
    raw = cpu_name.lower()
    norm = normalize(cpu_name)

    # ✅ 0. TWARDY WYJĄTEK – INTEL N (STOP PRZETWARZANIA)
    for n_model in INTEL_N_FORCE_OK:
        if n_model in raw:
            return "VERY_GOOD"

    # 🔴 1. BEZWZGLĘDNE ODRZUCENIE 2-RDZENIOWYCH
    for model in DUAL_CORE_CPUS:
        if model in norm:
            return "NO"

    # 🔴 2. Celeron / Atom
    if "celeron" in norm or "atom" in norm:
        return "NO"

    # 🍎 3. Apple Silicon
    if re.search(r"\bm[123]\b", raw) or "apple m" in raw:
        return "VERY_GOOD"

    # 📱 4. Snapdragon
    if "snapdragon x" in raw:
        return "VERY_GOOD"
    if "snapdragon" in raw:
        return "NO"

    # 🧠 5. Intel Core Ultra
    if "core ultra" in raw:
        return "VERY_GOOD"

    # ⚙️ 6. Intel Core (4C+)
    model = extract_intel_model(raw)
    if model:
        if model in INTEL_SPECIAL_OK:
            return "VERY_GOOD"

        gen = extract_intel_generation(model)
        if gen is None:
            return "UNKNOWN"

        if model.startswith("i3"):
            return "OK"

        if model.startswith("i5"):
            if gen in (8, 9):
                return "OK"
            return "VERY_GOOD"

        if model.startswith("i7"):
            return "VERY_GOOD"

        if model.startswith("i9"):
            return "VERY_GOOD"

    # 🔧 7. AMD Ryzen (4C+)
    if "ryzen" in norm:
        m = re.search(r"ryzen\s*([3579])", norm)
        if not m:
            return "UNKNOWN"
        return "OK" if m.group(1) == "3" else "VERY_GOOD"

    return "UNKNOWN"

# ==================================================
# PUBLIC API
# ==================================================

def evaluate_hardware(user_input: str) -> str:
    if "," not in user_input:
        return "❌ Podaj dane w formacie: `CPU, 8GB RAM`"

    cpu, ram = [x.strip() for x in user_input.split(",", 1)]
    ram_gb = extract_ram_gb(ram)

    if ram_gb is None:
        return "❌ Nie wykryto ilości RAM (np. 8GB)."

    if ram_gb < 8:
        return "❌ Za mało RAM (minimum 8 GB)."

    result = evaluate_cpu(cpu)

    if result == "NO":
        return "❌ Procesor zbyt słaby na Roblox Studio."

    if result == "OK":
        return "✅ Roblox Studio będzie działał poprawnie."

    if result == "VERY_GOOD":
        return "🚀 Roblox Studio będzie działał bardzo płynnie."

    log_unknown_cpu(cpu, ram_gb)
    return "❓ Procesor nieznany – zapisano do analizy. Zapytaj o ten konkretny przypadek na czacie - URGENT."


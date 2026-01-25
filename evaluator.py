import re
import os
import requests
from datetime import datetime

# ==================================================
# LISTY WYJĄTKÓW – TYLKO MODELE 2-RDZENIOWE
# ==================================================

INTEL_DUAL_CORE_ONLY = {
    # i7 – 2 rdzenie
    "i7-6500u",
    "i7-6600u",
    "i7-7500u",
    "i7-7600u",

    # i5 – 2 rdzenie
    "i5-6200u",
    "i5-6300u",
    "i5-7200u",
    "i5-7300u",

    # i3 – stare
    "i3-6100u",
    "i3-7100u",
    "i3-8130u",
    "i3-8145u",

    # Y-series
    "i5-8200y",
    "i5-8210y",
    "i7-8500y",
    "i7-8600y",
}

AMD_DUAL_CORE_ONLY = {
    "ryzen32200u",
    "ryzen32300u",
    "ryzen32200ge",
    "ryzen32250u",
    "ryzenr1505g",
    "ryzenr1606g",
}

GSHEET_WEBHOOK_URL = os.environ.get("GSHEET_WEBHOOK_URL")

# ==================================================
# POMOCNICZE
# ==================================================

def normalize(text: str) -> str:
    return text.lower().replace(" ", "")

def extract_ram_gb(text: str):
    match = re.search(r"(\d+)\s*gb", text.lower())
    return int(match.group(1)) if match else None

# ==================================================
# GOOGLE SHEETS LOGGER
# ==================================================

def log_unknown_cpu(cpu: str, ram: int):
    if not GSHEET_WEBHOOK_URL:
        return

    payload = {
        "cpu": cpu,
        "ram": ram,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
    }

    try:
        requests.post(GSHEET_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass

# ==================================================
# OCENA CPU – GŁÓWNA LOGIKA
# ==================================================

def evaluate_cpu(cpu_name: str) -> str:
    cpu_raw = cpu_name.lower()
    cpu_norm = normalize(cpu_name)

    # =========================
    # XEON – ręczna analiza
    # =========================
    if "xeon" in cpu_norm:
        return "UNKNOWN"

    # =========================
    # APPLE SILICON
    # =========================
    if re.search(r"\bm[123]\b", cpu_raw) or "applem" in cpu_norm:
        return "VERY_GOOD"

    # =========================
    # INTEL CORE ULTRA
    # =========================
    if "coreultra" in cpu_norm:
        return "VERY_GOOD"

    # =========================
    # SNAPDRAGON
    # =========================
    if "snapdragonxelite" in cpu_norm or "snapdragonxplus" in cpu_norm:
        return "VERY_GOOD"
    if "snapdragon" in cpu_norm:
        return "NO"

    # =========================
    # ODRZUCENIE – TYLKO 2 RDZENIE
    # =========================
    for model in INTEL_DUAL_CORE_ONLY:
        if model in cpu_norm:
            return "NO"

    for model in AMD_DUAL_CORE_ONLY:
        if model in cpu_norm:
            return "NO"

    # =========================
    # INTEL CORE – OCENA JAKOŚCIOWA
    # =========================
    match = re.search(r"(i[3579])-(\d{4,5})", cpu_norm)
    if match:
        tier = match.group(1)      # i3 / i5 / i7 / i9
        model = match.group(2)

        # generacja tylko do jakości
        if model.startswith(("10", "11", "12", "13", "14")):
            gen = int(model[:2])
        else:
            gen = int(model[0])

        if tier == "i3":
            return "OK"

        if tier == "i5":
            if gen <= 7:
                return "WEAK"
            if gen <= 9:
                return "OK"
            return "VERY_GOOD"

        if tier == "i7":
            if gen <= 7:
                return "OK"
            return "VERY_GOOD"

        if tier == "i9":
            return "VERY_GOOD"

    # =========================
    # AMD RYZEN (PO WYJĄTKACH)
    # =========================
    if "ryzen" in cpu_norm:
        match = re.search(r"ryzen([3579])(\d{4})", cpu_norm)
        if not match:
            return "UNKNOWN"

        tier = int(match.group(1))
        return "OK" if tier == 3 else "VERY_GOOD"

    # =========================
    # CELERON / ATOM
    # =========================
    if "celeron" in cpu_norm or "atom" in cpu_norm:
        return "NO"

    return "UNKNOWN"

# ==================================================
# GŁÓWNA FUNKCJA (CPU + RAM)
# ==================================================

def evaluate_hardware(user_input: str) -> str:
    if "," not in user_input:
        return "❌ Podaj dane w formacie: `CPU, 8GB RAM`"

    cpu_part, ram_part = [x.strip() for x in user_input.split(",", 1)]
    ram_gb = extract_ram_gb(ram_part)

    if ram_gb is None:
        return "❌ Nie wykryto ilości RAM (np. 8GB)."

    if ram_gb < 8:
        return "❌ Za mało RAM (minimum 8 GB)."

    cpu_result = evaluate_cpu(cpu_part)

    if cpu_result == "NO":
        return "❌ Procesor zbyt słaby na Roblox Studio."

    if cpu_result == "WEAK":
        return (
            "⚠️ Roblox Studio uruchomi się,\n"
            "ale przy większych projektach\n"
            "mogą wystąpić spadki wydajności."
        )

    if cpu_result == "OK":
        return "✅ Roblox Studio będzie działał stabilnie."

    if cpu_result == "VERY_GOOD":
        return "🚀 Roblox Studio będzie działał bardzo płynnie."

    log_unknown_cpu(cpu_part, ram_gb)
    return "❓ Procesor nieznany – zapisano do analizy. Zapytaj o ten konkretny przypadek na czacie - URGENT. "

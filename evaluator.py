import re
import os
import requests
from datetime import datetime

# ==================================================
# INTEL – TWARDO ODRZUCANE (ZBYT SŁABE)
# ==================================================

INTEL_HARD_REJECT = {
    "i3-6100u",
    "i3-7100u",
    "i3-8130u",
    "i3-8145u",
    "i5-4300u",
    "i5-4200u",
}

# ==================================================
# INTEL / AMD – DUAL CORE (WARUNKOWO / SŁABE)
# ==================================================

INTEL_DUAL_CORE_EXCEPTIONS = {
    "i5-6200u", "i5-6300u", "i5-6267u", "i5-6287u",
    "i5-7200u", "i5-7267u", "i5-7287u", "i5-7300u", "i5-7360u",
    "i5-8200y", "i5-8210y",
    "i7-6500u", "i7-6600u",
    "i7-7500u", "i7-7600u", "i7-7660u",
    "i7-8500y", "i7-8600y",
}

AMD_DUAL_CORE_EXCEPTIONS = {
    "ryzen 3 2200u",
    "ryzen 3 2300u",
    "ryzen r1505g",
    "ryzen r1606g",
}

# ==================================================
# SPECJALNE MODELE OK
# ==================================================

INTEL_SPECIAL_OK = {
    "pentium gold 8505",
    "n95",
    "n350",
    "n355",
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

def extract_intel_generation(cpu: str):
    match = re.search(r"i[3579]-(\d{4,5})", cpu)
    if not match:
        return None

    model = match.group(1)
    return int(model[:2]) if len(model) == 5 else int(model[0])

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
# OCENA CPU
# ==================================================

def evaluate_cpu(cpu_name: str) -> str:
    cpu_raw = cpu_name.lower()
    cpu_norm = normalize(cpu_name)

    # ---------- XEON ----------
    if "xeon" in cpu_raw:
        return "UNKNOWN"

    # ---------- INTEL CORE ULTRA ----------
    if "core ultra" in cpu_raw:
        return "VERY_GOOD"

    # ---------- SNAPDRAGON ----------
    if "snapdragon x elite" in cpu_raw or "snapdragon x plus" in cpu_raw:
        return "VERY_GOOD"
    if "snapdragon" in cpu_raw:
        return "NO"

    # ---------- HARD REJECT ----------
    for model in INTEL_HARD_REJECT:
        if model in cpu_norm:
            return "NO"

    # ---------- DUAL CORE EXCEPTIONS ----------
    for model in INTEL_DUAL_CORE_EXCEPTIONS:
        if model in cpu_norm:
            return "WEAK"

    for model in AMD_DUAL_CORE_EXCEPTIONS:
        if model in cpu_raw:
            return "WEAK"

    # ---------- INTEL SPECIAL OK ----------
    for model in INTEL_SPECIAL_OK:
        if model in cpu_norm:
            return "VERY_GOOD"

    # ---------- AMD RYZEN ----------
    if "ryzen" in cpu_raw:
        match = re.search(r"ryzen\s+([3579])\s+(\d{4})", cpu_raw)
        if not match:
            return "UNKNOWN"

        tier = int(match.group(1))
        series = int(match.group(2))

        if tier == 3:
            return "OK"
        return "VERY_GOOD"

    # ---------- INTEL CORE ----------
    if cpu_raw.startswith(("i3", "i5", "i7", "i9")):
        gen = extract_intel_generation(cpu_raw)
        if gen is None:
            return "UNKNOWN"

        if cpu_raw.startswith("i3"):
            return "OK" if gen >= 10 else "NO"

        if cpu_raw.startswith("i5"):
            if gen in (6, 7):
                return "WEAK"
            if gen in (8, 9):
                return "OK"
            return "VERY_GOOD"

        if cpu_raw.startswith("i7"):
            return "OK" if gen in (6, 7) else "VERY_GOOD"

        if cpu_raw.startswith("i9"):
            return "VERY_GOOD"

    return "UNKNOWN"

# ==================================================
# GŁÓWNA FUNKCJA
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
        return "⚠️ Sprzęt spełnia minimum, ale mogą wystąpić spadki wydajności."

    if cpu_result == "OK":
        return "✅ Roblox Studio będzie działał poprawnie."

    if cpu_result == "VERY_GOOD":
        return "🚀 Roblox Studio będzie działał bardzo płynnie."

    log_unknown_cpu(cpu_part, ram_gb)
    return "❓ Procesor nieznany – zapisano do analizy."

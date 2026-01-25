import re
import os
import requests
from datetime import datetime

# ==================================================
# INTEL – TWARDO ODRZUCANE (STARE, SŁABE)
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
# INTEL – STARE DUAL CORE (ZBYT SŁABE)
# ==================================================

INTEL_DUAL_CORE_EXCEPTIONS = {
    "i5-6200u", "i5-6300u", "i5-6267u", "i5-6287u",
    "i5-7200u", "i5-7267u", "i5-7287u", "i5-7300u", "i5-7360u",
    "i5-8200y", "i5-8210y",
    "i7-6500u", "i7-6600u",
    "i7-7500u", "i7-7600u", "i7-7660u",
    "i7-8500y", "i7-8600y",
}

# ==================================================
# SPECJALNE MODELE OK
# ==================================================

INTEL_SPECIAL_OK = {
    "pentiumgold8505",
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

def cpu_clean(text: str) -> str:
    return text.lower().replace(" ", "")

def extract_ram_gb(text: str):
    m = re.search(r"(\d+)\s*gb", text.lower())
    return int(m.group(1)) if m else None

def extract_intel_model(cpu: str):
    m = re.search(r"i[3579]-\d{4,5}[a-z]*", cpu)
    return m.group(0) if m else None

def extract_intel_generation(cpu: str):
    m = re.search(r"i[3579]-(\d{4,5})", cpu)
    if not m:
        return None

    model = m.group(1)

    # 10–14 generacja
    if model.startswith(("10", "11", "12", "13", "14")):
        return int(model[:2])

    # 6–9 generacja
    return int(model[0])

# ==================================================
# GOOGLE SHEETS LOGGER
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
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
            },
            timeout=5,
        )
    except Exception:
        pass

# ==================================================
# OCENA CPU
# ==================================================

def evaluate_cpu(cpu_name: str) -> str:
    raw = cpu_name.lower()
    norm = normalize(cpu_name)
    clean = cpu_clean(cpu_name)

    intel_model = extract_intel_model(clean)

    # ---------- blacklist ----------
    if intel_model:
        if intel_model in INTEL_HARD_REJECT:
            return "NO"
        if intel_model in INTEL_DUAL_CORE_EXCEPTIONS:
            return "NO"

    # ---------- Apple Silicon ----------
    if re.search(r"\bm[123]\b", raw) or "applem" in norm:
        return "VERY_GOOD"

    # ---------- Intel Core Ultra ----------
    if "coreultra" in norm:
        return "VERY_GOOD"

    # ---------- Snapdragon ----------
    if "snapdragonxelite" in norm or "snapdragonxplus" in norm:
        return "VERY_GOOD"
    if "snapdragon" in norm:
        return "NO"

    # ---------- Intel special ----------
    for m in INTEL_SPECIAL_OK:
        if m in norm:
            return "VERY_GOOD"

    # ---------- AMD Ryzen ----------
    if "ryzen" in norm:
        m = re.search(r"ryzen([3579])(\d{4})", norm)
        if not m:
            return "UNKNOWN"
        return "OK" if int(m.group(1)) == 3 else "VERY_GOOD"

    # ---------- Intel Core ----------
    if intel_model:
        gen = extract_intel_generation(clean)
        if gen is None or gen < 6:
            return "NO"

        if intel_model.startswith("i3-"):
            return "OK" if gen >= 10 else "NO"

        if intel_model.startswith("i5-"):
            if gen in (6, 7):
                return "NO"
            if gen in (8, 9):
                return "OK"
            return "VERY_GOOD"

        if intel_model.startswith("i7-"):
            return "NO" if gen in (6, 7) else "VERY_GOOD"

        if intel_model.startswith("i9-"):
            return "VERY_GOOD"

    if "celeron" in norm or "atom" in norm:
        return "NO"

    return "UNKNOWN"

# ==================================================
# GŁÓWNA FUNKCJA
# ==================================================

def evaluate_hardware(user_input: str) -> str:
    if "," not in user_input:
        return "❌ Podaj dane w formacie: `CPU, 8GB RAM`"

    cpu, ram_txt = [x.strip() for x in user_input.split(",", 1)]
    ram = extract_ram_gb(ram_txt)

    if ram is None:
        return "❌ Nie wykryto ilości RAM (np. 8GB)."
    if ram < 8:
        return "❌ Za mało RAM (minimum 8 GB)."

    result = evaluate_cpu(cpu)

    if result == "NO":
        return "❌ Procesor zbyt słaby na Roblox Studio."
    if result == "OK":
        return "✅ Roblox Studio będzie działał poprawnie."
    if result == "VERY_GOOD":
        return "🚀 Roblox Studio będzie działał bardzo płynnie."

    log_unknown_cpu(cpu, ram)
    return "❓ Procesor nieznany – zapisano do analizy. Zapytaj o ten konkretny przypadek na czacie - URGENT. "

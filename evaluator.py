import re
import os
import requests
from datetime import datetime

# ===============================
# HARD REJECT – ZAWSZE NIE
# ===============================

INTEL_HARD_REJECT = {
    "i3-6100u", "i3-7100u", "i3-8130u", "i3-8145u",
    "i5-4200u", "i5-4300u",
}

INTEL_DUAL_CORE_EXACT = {
    "i5-6200u", "i5-6300u", "i5-6267u", "i5-6287u",
    "i5-7200u", "i5-7267u", "i5-7287u", "i5-7300u", "i5-7360u",
    "i5-8200y", "i5-8210y",
    "i7-6500u", "i7-6600u",
    "i7-7500u", "i7-7600u", "i7-7660u",
    "i7-8500y", "i7-8600y",
}

AMD_DUAL_CORE = {
    "ryzen32200u",
    "ryzen32300u",
    "ryzenr1505g",
    "ryzenr1606g",
}

INTEL_SPECIAL_OK = {
    "pentiumgold8505",
    "n95", "n350", "n355",
}

GSHEET_WEBHOOK_URL = os.environ.get("GSHEET_WEBHOOK_URL")

# ===============================
# HELPERS
# ===============================

def normalize(text: str) -> str:
    return text.lower().replace(" ", "")

def extract_ram_gb(text: str):
    m = re.search(r"(\d+)\s*gb", text.lower())
    return int(m.group(1)) if m else None

def extract_intel_generation(cpu: str):
    m = re.search(r"i[3579]-(\d{4,5})", cpu)
    if not m:
        return None
    model = m.group(1)
    return int(model[:2]) if len(model) == 5 else int(model[0])

# ===============================
# GOOGLE SHEETS
# ===============================

def log_unknown_cpu(cpu: str, ram: int):
    if not GSHEET_WEBHOOK_URL:
        return
    try:
        requests.post(
            GSHEET_WEBHOOK_URL,
            json={"cpu": cpu, "ram": ram, "date": datetime.utcnow().isoformat()},
            timeout=5
        )
    except Exception:
        pass

# ===============================
# CPU EVALUATION
# ===============================

def evaluate_cpu(cpu_name: str) -> str:
    cpu_raw = cpu_name.lower()
    cpu_norm = normalize(cpu_name)

    # --- absolutne odrzucenia
    if "celeron" in cpu_norm or "atom" in cpu_norm:
        return "NO"

    if "xeon" in cpu_norm:
        return "UNKNOWN"

    # --- Apple Silicon
    if re.search(r"\bm[123]\b", cpu_raw) or "applem" in cpu_norm:
        return "VERY_GOOD"

    # --- Core Ultra
    if "coreultra" in cpu_norm:
        return "VERY_GOOD"

    # --- Snapdragon
    if "snapdragonx" in cpu_norm:
        return "VERY_GOOD"
    if "snapdragon" in cpu_norm:
        return "NO"

    # --- dokładne wyjątki
    if cpu_norm in INTEL_HARD_REJECT:
        return "NO"
    if cpu_norm in INTEL_DUAL_CORE_EXACT:
        return "NO"
    if cpu_norm in AMD_DUAL_CORE:
        return "NO"
    if cpu_norm in INTEL_SPECIAL_OK:
        return "VERY_GOOD"

    # --- AMD Ryzen
    if "ryzen" in cpu_norm:
        m = re.search(r"ryzen([3579])(\d{4})", cpu_norm)
        if not m:
            return "UNKNOWN"
        tier = int(m.group(1))
        return "OK" if tier == 3 else "VERY_GOOD"

    # --- Intel Core
    gen = extract_intel_generation(cpu_norm)
    if gen is None:
        return "UNKNOWN"

    if "i3-" in cpu_norm:
        return "OK" if gen >= 10 else "NO"

    if "i5-" in cpu_norm:
        if gen in (6, 7):
            return "NO"
        if gen in (8, 9):
            return "OK"
        return "VERY_GOOD"

    if "i7-" in cpu_norm:
        return "OK" if gen in (6, 7) else "VERY_GOOD"

    if "i9-" in cpu_norm:
        return "VERY_GOOD"

    return "UNKNOWN"

# ===============================
# HARDWARE
# ===============================

def evaluate_hardware(user_input: str) -> str:
    if "," not in user_input:
        return "❌ Podaj dane w formacie: `CPU, 8GB RAM`"

    cpu, ram = [x.strip() for x in user_input.split(",", 1)]
    ram_gb = extract_ram_gb(ram)

    if ram_gb is None:
        return "❌ Nie wykryto ilości RAM."
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

import re
import os
import requests
from datetime import datetime

# ==================================================
# WYJĄTKI – INTEL DUAL CORE (6 GEN +)
# ==================================================

INTEL_DUAL_CORE_EXCEPTIONS = {
    #6/7/8 gen - i5
    "i5-6200u",
    "i5-6300u",
    "i5-6267u",
    "i5-6287u",
    "i5-7200u",
    "i5-7267u",
    "i5-7287u",
    "i5-7300u",
    "i5-7360u",
    "i5-8200y",
    "i5-8210y",

    #6/7/8 gen - i7
    "i7-6500u",
    "i7-6600u",
    "i7-7500u",
    "i7-7600u",
    "i7-7660u",
    "i7-8500y",
    "i7-8600y",
    
    # 9/10 gen – i5
    "i5-10110u",
    "i5-10200u",
    "i5-1030g4",
    "i5-1030g7",
    "i5-1038ng7",

    # 9/10 gen – i7
    "i7-10510u",
    "i7-1060g7",
    "i7-1068ng7",

    # others
    "Pentium Gold 7505",
    "Pnetium Gold 6405U",
}

INTEL_SPECIAL_OK = {
    "pentium gold 8505": 5,
    "n95": 4,
    "n350": 8,
    "n355": 8,
}

GSHEET_WEBHOOK_URL = os.environ.get("GSHEET_WEBHOOK_URL")

# ==================================================
# POMOCNICZE
# ==================================================

def normalize(text: str) -> str:
    return text.lower().replace(" ", "")

def extract_cores_from_text(text: str):
    text = text.lower()

    for pattern in [
        r"(\d+)\s*[-]?\s*cores?",
        r"\b(\d+)\s*c\b",
        r"(\d+)\s*p\s*\+\s*(\d+)\s*e",
    ]:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:
                return int(match.group(1)) + int(match.group(2))
            return int(match.group(1))
    return None

def extract_ram_gb(text: str):
    match = re.search(r"(\d+)\s*gb", text.lower())
    return int(match.group(1)) if match else None

# ==================================================
# GOOGLE SHEETS LOGGER (PRODUCTION)
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

    if "xeon" in cpu_raw:
        return "UNKNOWN"

    for model in INTEL_DUAL_CORE_EXCEPTIONS:
        if model in cpu_norm:
            return "NO"

    for model, cores in INTEL_SPECIAL_OK.items():
        if model.replace(" ", "") in cpu_norm:
            return "OK" if cores >= 4 else "NO"
            
    if "core ultra" in cpu_raw:
        return "OK"

    if "snapdragon x elite" in cpu_raw or "snapdragon x plus" in cpu_raw:
        return "OK"

    if "snapdragon" in cpu_raw:
        return "NO"


    if "ryzen" in cpu_raw:
        if "ryzen 9" in cpu_raw or "ryzen 7" in cpu_raw or "ryzen 5" in cpu_raw:
            return "OK"

    # Ryzen 3 – potencjalnie za słaby
    if "ryzen 3" in cpu_raw:
        return "NO"

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
        return f"❌ Za mało RAM: {ram_gb} GB (minimum 8 GB)."

    cpu_result = evaluate_cpu(cpu_part)

    if cpu_result == "OK":
        return (
            "✅ *Sprzęt spełnia wymagania Roblox Studio*\n\n"
            f"CPU: **{cpu_part}**\n"
            f"RAM: **{ram_gb} GB**"
        )

    if cpu_result == "NO":
        return (
            "❌ *Procesor zbyt słaby na Roblox Studio*\n\n"
            f"CPU: **{cpu_part}**\n"
            "Wymagane minimum: **4 rdzenie CPU**"
        )

    # UNKNOWN
    log_unknown_cpu(cpu_part, ram_gb)
    return (
        "❓ *Nie udało się jednoznacznie ocenić procesora*\n\n"
        f"CPU: **{cpu_part}**\n"
        "Model został zapisany do dalszej analizy."
    )

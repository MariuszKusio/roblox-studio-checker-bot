import re
import os
import requests
from datetime import datetime

# ==================================================
# WYJĄTKI – INTEL DUAL CORE (6 GEN +)
# ==================================================

INTEL_DUAL_CORE_EXCEPTIONS = {
    "i5-6200u", "i5-6300u", "i5-6267u", "i5-6287u",
    "i5-7200u", "i5-7267u", "i5-7287u", "i5-7300u", "i5-7360u",
    "i5-8200y", "i5-8210y",
    "i7-6500u", "i7-6600u",
    "i7-7500u", "i7-7600u", "i7-7660u",
    "i7-8500y", "i7-8600y",
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

    if "xeon" in cpu_raw:
        return "UNKNOWN"

    for model in INTEL_DUAL_CORE_EXCEPTIONS:
        if model in cpu_norm:
            return "NO"

    for model, cores in INTEL_SPECIAL_OK.items():
        if model.replace(" ", "") in cpu_norm:
            return "OK" if cores >= 4 else "NO"

    if "ryzen" in cpu_raw or cpu_raw.startswith(("i3", "i5", "i7", "i9")):
        cores = extract_cores_from_text(cpu_raw)
        if cores is None:
            return "UNKNOWN"
        return "OK" if cores >= 4 else "NO"

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
        return f"✅ Sprzęt spełnia wymagania\nCPU: {cpu_part}\nRAM: {ram_gb} GB"

    if cpu_result == "NO":
        return f"❌ Procesor zbyt słaby\nCPU: {cpu_part}"

    # UNKNOWN
    log_unknown_cpu(cpu_part, ram_gb)
    return (
        "❓ Nie udało się jednoznacznie ocenić procesora\n\n"
        f"CPU: {cpu_part}\n"
        "Model zapisany do dalszej analizy."
    )

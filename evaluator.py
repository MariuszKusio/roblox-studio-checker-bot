from parser import extract_ram, is_ram_ok, extract_cpu_profile
import re
from datetime import datetime
import json
import os

# ==================================================
# 1. BAZA WYJĄTKÓW – INTEL DUAL CORE (6 GEN +)
# ==================================================

INTEL_DUAL_CORE_EXCEPTIONS = {
    # i5 – 6 gen
    "i5-6200u",
    "i5-6300u",
    "i5-6267u",
    "i5-6287u",

    # i5 – 7 gen
    "i5-7200u",
    "i5-7267u",
    "i5-7287u",
    "i5-7300u",
    "i5-7360u",

    # i5 – Y series
    "i5-8200y",
    "i5-8210y",

    # i7 – 6 gen
    "i7-6500u",
    "i7-6600u",

    # i7 – 7 gen
    "i7-7500u",
    "i7-7600u",
    "i7-7660u",

    # i7 – Y series
    "i7-8500y",
    "i7-8600y",
}

# ==================================================
# 2. WYJĄTKI POZYTYWNE (POTWIERDZONE RDZENIE)
# ==================================================

INTEL_SPECIAL_OK = {
    "pentium gold 8505": 5,   # 1P + 4E
    "n95": 4,
    "n350": 8,
    "n355": 8,
}

# ==================================================
# 3. POMOCNICZE
# ==================================================

def normalize(text: str) -> str:
    return text.lower().replace(" ", "")


def extract_cores_from_text(text: str):
    text = text.lower()

    # np. "4 cores", "6-core"
    match = re.search(r"(\d+)\s*[-]?\s*cores?", text)
    if match:
        return int(match.group(1))

    # np. "6C/12T"
    match = re.search(r"\b(\d+)\s*c\b", text)
    if match:
        return int(match.group(1))

    # hybrid: "1P+4E"
    match = re.search(r"(\d+)\s*p\s*\+\s*(\d+)\s*e", text)
    if match:
        return int(match.group(1)) + int(match.group(2))

    return None


# ==================================================
# 4. OCENA CPU
# ==================================================

def evaluate_cpu(cpu_name: str) -> str:
    cpu_raw = cpu_name.lower()
    cpu_norm = normalize(cpu_name)

    # Xeon – ręczna weryfikacja
    if "xeon" in cpu_raw:
        return "UNKNOWN"

    # Jawne wyjątki dual-core
    for model in INTEL_DUAL_CORE_EXCEPTIONS:
        if model in cpu_norm:
            return "NO"

    # Jawne wyjątki pozytywne
    for model, cores in INTEL_SPECIAL_OK.items():
        if model.replace(" ", "") in cpu_norm:
            return "OK" if cores >= 4 else "NO"

    # AMD Ryzen
    if "ryzen" in cpu_raw:
        cores = extract_cores_from_text(cpu_raw)
        if cores is None:
            return "UNKNOWN"
        return "OK" if cores >= 4 else "NO"

    # Intel Core (i3/i5/i7/i9)
    if cpu_raw.startswith(("i3", "i5", "i7", "i9")):
        cores = extract_cores_from_text(cpu_raw)
        if cores is None:
            return "UNKNOWN"
        return "OK" if cores >= 4 else "NO"

    return "UNKNOWN"


# ==================================================
# 5. OCENA RAM
# ==================================================

def extract_ram_gb(text: str):
    match = re.search(r"(\d+)\s*gb", text.lower())
    if match:
        return int(match.group(1))
    return None


# ==================================================
# 6. GŁÓWNA FUNKCJA – UŻYWANA PRZEZ BOTA
# ==================================================

def evaluate_hardware(user_input: str) -> str:
    """
    Oczekiwany format:
    'i5-8250U, 8GB RAM'
    """

    if "," not in user_input:
        return (
            "❌ *Niepoprawny format danych*\n\n"
            "Podaj dane w formacie:\n"
            "`model procesora, ilość RAM`\n\n"
            "Przykład:\n"
            "`i5-8250U, 8GB RAM`"
        )

    cpu_part, ram_part = [x.strip() for x in user_input.split(",", 1)]

    ram_gb = extract_ram_gb(ram_part)
    if ram_gb is None:
        return "❌ Nie wykryto ilości pamięci RAM (np. `8GB`)."

    if ram_gb < 8:
        return (
            f"❌ *Za mało pamięci RAM*\n\n"
            f"Wykryto: **{ram_gb} GB RAM**\n"
            "Minimalne wymaganie: **8 GB RAM**"
        )

    cpu_result = evaluate_cpu(cpu_part)

   if cpu_result == "OK":
        return (
            "✅ *Sprzęt spełnia wymagania Roblox Studio*\n\n"
            f"• Procesor: **{cpu_part}**\n"
            f"• RAM: **{ram_gb} GB**"
        )

    if cpu_result == "NO":
        return (
            "❌ *Procesor zbyt słaby*\n\n"
            f"Wykryty model: **{cpu_part}**\n"
            "Wymagane minimum: **4 rdzenie CPU**"
        )

    # 👇 TUTAJ LOGUJEMY UNKNOWN
    log_unknown_cpu(cpu_part, ram_gb)

    return (
        "❓ *Nie udało się jednoznacznie ocenić procesora*\n\n"
        f"Wykryty model: **{cpu_part}**\n\n"
        "Ten procesor wymaga ręcznej weryfikacji.\n"
        "Sprawdź liczbę rdzeni w specyfikacji producenta."
    )


LOG_FILE = "unknown_cpu.log"

def log_unknown_cpu(cpu: str, ram: int):
    entry = {
        "cpu": cpu,
        "ram": ram,
        "date": datetime.utcnow().strftime("%Y-%m-%d")
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        # logowanie nie może nigdy zepsuć działania bota
        pass

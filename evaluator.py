import re
import os
import requests
from datetime import datetime

# ==================================================
# WYJĄTKI – INTEL DUAL CORE (6 GEN +)
# ==================================================

INTEL_HARD_REJECT = {
    # stare i3 (2 rdzenie)
    "i3-6100u",
    "i3-7100u",
    "i3-8130u",
    "i3-8145u",

    # bardzo stare / energooszczędne
    "i5-4300u",
    "i5-4200u",
}

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

AMD_DUAL_CORE_EXCEPTIONS = {
    "ryzen 3 2200u",
    "ryzen 3 2300u",
    "ryzen r1505g",
    "ryzen r1606g",
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
# Funkcja da samych ryzenów
# ==================================================

def extract_ryzen_series(cpu: str):
    match = re.search(r"ryzen\s+\d\s+(\d{4})", cpu.lower())
    if match:
        return int(match.group(1))
    return None


# ==================================================
# INTEL – WYCIĄGANIE GENERACJI (POPRAWNE)
# ==================================================

def extract_intel_generation(cpu: str):
    """
    Zwraca generację procesora Intel Core:
    6,7,8,9,10,11,12,13...
    """
    match = re.search(r"i[3579]-(\d{4,5})", cpu.lower())
    if not match:
        return None

    model_number = match.group(1)

    # 6–9 gen → pierwsza cyfra
    if len(model_number) == 4:
        return int(model_number[0])

    # 10+ gen → pierwsze dwie cyfry
    return int(model_number[:2])


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

    # =========================
    # XEON
    # =========================
    if "xeon" in cpu_raw:
        return "UNKNOWN"

    # =========================
    # INTEL CORE ULTRA
    # =========================
    if "core ultra" in cpu_raw:
        return "VERY_GOOD"

    # =========================
    # SNAPDRAGON
    # =========================
    if "snapdragon x elite" in cpu_raw or "snapdragon x plus" in cpu_raw:
        return "VERY_GOOD"

    if "snapdragon" in cpu_raw:
        return "NO"

    # =========================
    # INTEL – TWARDO ODRZUCANE
    # =========================
    for model in INTEL_HARD_REJECT:
        if model in cpu_norm:
            return "NO"

    # =========================
    # INTEL – SPECJALNE MODELE OK
    # =========================
    for model in INTEL_SPECIAL_OK:
        if model.replace(" ", "") in cpu_norm:
            return "VERY_GOOD"

    # =========================
    # AMD RYZEN
    # =========================
    if "ryzen" in cpu_raw:
        match = re.search(r"ryzen\s+[3579]\s+(\d{4})", cpu_raw)
        if not match:
            return "UNKNOWN"

        series = int(match.group(1))

        if series >= 4000:
            if "ryzen 3" in cpu_raw:
                return "OK"
            return "VERY_GOOD"

        return "WEAK"

    # =========================
    # INTEL CORE i3 / i5 / i7 / i9
    # =========================
    if cpu_raw.startswith(("i3", "i5", "i7", "i9")):
        gen = extract_intel_generation(cpu_raw)
        if gen is None:
            return "UNKNOWN"


        # i3
        if cpu_raw.startswith("i3"):
            if gen >= 10:
                return "OK"
            return "NO"

        # i5
        if cpu_raw.startswith("i5"):
            if gen in (6, 7):
                return "WEAK"
            if gen in (8, 9):
                return "OK"
            if gen >= 10:
                return "VERY_GOOD"

        # i7
        if cpu_raw.startswith("i7"):
            if gen in (6, 7):
                return "OK"
            if gen >= 8:
                return "VERY_GOOD"

        # i9
        if cpu_raw.startswith("i9"):
            return "VERY_GOOD"

    # =========================
    # FALLBACK
    # =========================
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
        return (
            "❌ *Za mało pamięci RAM*\n\n"
            f"Wykryto: **{ram_gb} GB RAM**\n"
            "Minimalne wymaganie: **8 GB RAM**"
        )

    cpu_result = evaluate_cpu(cpu_part)

    # =========================
    # CPU – ZBYT SŁABY
    # =========================
    if cpu_result == "NO":
        return (
            "❌ *Procesor zbyt słaby na Roblox Studio*\n\n"
            f"CPU: **{cpu_part}**\n"
            "Roblox Studio nie będzie działał poprawnie\n"
            "w projektach realizowanych na kursie."
        )

    # =========================
    # CPU – WARUNKOWO
    # =========================
    if cpu_result == "WEAK":
        return (
            "⚠️ *Sprzęt spełnia minimalne wymagania*\n\n"
            f"CPU: **{cpu_part}**\n"
            "Roblox Studio uruchomi się, jednak przy większych\n"
            "projektach (np. rozbudowane mapy) mogą wystąpić\n"
            "znaczące spadki wydajności."
        )

    # =========================
    # CPU – OK
    # =========================
    if cpu_result == "OK":
        return (
            "✅ *Sprzęt odpowiedni do pracy w Roblox Studio*\n\n"
            f"CPU: **{cpu_part}**\n"
            "Praca przy średnich i większych projektach\n"
            "powinna przebiegać stabilnie."
        )

    # =========================
    # CPU – BARDZO DOBRY
    # =========================
    if cpu_result == "VERY_GOOD":
        return (
            "🚀 *Sprzęt bardzo dobrze nadaje się do Roblox Studio*\n\n"
            f"CPU: **{cpu_part}**\n"
            "Roblox Studio będzie działał płynnie nawet\n"
            "przy złożonych projektach oraz jednoczesnej\n"
            "pracy na Zoomie."
        )

    # =========================
    # CPU – NIEZNANY (TYLKO TU)
    # =========================
    log_unknown_cpu(cpu_part, ram_gb)
    return (
        "❓ *Nie udało się jednoznacznie ocenić procesora*\n\n"
        f"CPU: **{cpu_part}**\n"
        "Model został zapisany do dalszej analizy."
    )

from parser import extract_ram, is_ram_ok, extract_cpu_profile


import re

# =========================
# BAZA WYJĄTKÓW – DUAL CORE
# =========================

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

# =========================
# WYJĄTKI POZYTYWNE
# =========================

INTEL_SPECIAL_OK = {
    "pentium gold 8505": 5,   # 1P + 4E
    "n95": 4,
    "n355": 8,
    "n350": 8,
}

# =========================
# POMOCNICZE
# =========================

def normalize_cpu_name(cpu: str) -> str:
    return cpu.lower().replace(" ", "")

def extract_cores_from_text(cpu: str):
    cpu = cpu.lower()

    # np. "4 cores", "6-core"
    match = re.search(r"(\d+)\s*[-]?\s*cores?", cpu)
    if match:
        return int(match.group(1))

    # np. "6C/12T"
    match = re.search(r"\b(\d+)\s*c\b", cpu)
    if match:
        return int(match.group(1))

    # hybrid: "1P+4E"
    match = re.search(r"(\d+)\s*p\s*\+\s*(\d+)\s*e", cpu)
    if match:
        return int(match.group(1)) + int(match.group(2))

    return None

# =========================
# GŁÓWNA OCENA CPU
# =========================

def evaluate_cpu(cpu_name: str) -> str:
    cpu_raw = cpu_name.lower()
    cpu_norm = normalize_cpu_name(cpu_name)

    # Xeon – specjalny przypadek
    if "xeon" in cpu_raw:
        return "UNKNOWN"

    # Jawne wyjątki 2-rdzeniowe
    for model in INTEL_DUAL_CORE_EXCEPTIONS:
        if model in cpu_norm:
            return "NO"

    # Jawne wyjątki pozytywne
    for model, cores in INTEL_SPECIAL_OK.items():
        if model.replace(" ", "") in cpu_norm:
            return "OK" if cores >= 4 else "NO"

    # Ryzen – ufamy rdzeniom
    if "ryzen" in cpu_raw:
        cores = extract_cores_from_text(cpu_raw)
        if cores is None:
            return "UNKNOWN"
        return "OK" if cores >= 4 else "NO"

    # Intel Core – domyślna reguła
    if cpu_raw.startswith(("i3", "i5", "i7", "i9")):
        cores = extract_cores_from_text(cpu_raw)
        if cores is None:
            return "UNKNOWN"
        return "OK" if cores >= 4 else "NO"

    # Inne przypadki
    return "UNKNOWN"

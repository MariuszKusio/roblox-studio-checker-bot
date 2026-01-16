import re

# ==================================================
# RAM
# ==================================================

def extract_ram(text: str):
    """
    Wyciąga ilość RAM z tekstu, np.:
    "8GB RAM", "16 gb", "mam 32GB"
    Zwraca int lub None
    """
    match = re.search(r"(\d+)\s?gb", text.lower())
    return int(match.group(1)) if match else None


def is_ram_ok(ram: int):
    """
    Minimalny warunek dla Roblox Studio:
    RAM >= 8 GB
    """
    return ram is not None and ram >= 8


# ==================================================
# INTEL CPU ANALYSIS
# ==================================================

def extract_intel_generation(text: str):
    """
    Próbuje wyciągnąć generację Intela z modelu:
    i5-8250U -> 8
    i7-7500U -> 7
    i3-10100 -> 10
    """
    match = re.search(r"i[3579]-([0-9]{4})", text.lower())
    if match:
        return int(match.group(1)[0])
    return None


def intel_cpu_profile(text: str):
    """
    Określa profil CPU + zintegrowanej grafiki dla Intela
    """
    t = text.lower()

    # --------------------------
    # Słabe serie (Celeron itd.)
    # --------------------------
    if "celeron" in t:
        # Wyjątek: n4xxx – bardzo słabe, ale uruchomi się
        if any(x in t for x in ["n4020", "n4100", "n4120"]):
            return "igpu_limited"
        return "igpu_bad"

    if "pentium" in t or "atom" in t:
        return "igpu_bad"

    # --------------------------
    # Xeon – nie zgadujemy
    # --------------------------
    if "xeon" in t:
        return "unknown"

    # --------------------------
    # Intel Core i3 / i5 / i7 / i9
    # --------------------------
    gen = extract_intel_generation(t)

    # Nie udało się ustalić generacji
    if gen is None:
        return "unknown"

    # Za stare – mobilne 2 rdzenie + słabe iGPU
    if gen < 7:
        return "igpu_bad"

    # 7+ generacja
    if "i3" in t:
        # i3 nawet nowe często są 2C/4T
        return "igpu_limited"

    if "i5" in t or "i7" in t or "i9" in t:
        return "igpu_ok"

    return "unknown"


# ==================================================
# AMD CPU ANALYSIS
# ==================================================

def amd_cpu_profile(text: str):
    """
    Określa profil CPU + zintegrowanej grafiki dla AMD
    """
    t = text.lower()

    # Ryzen (Vega iGPU)
    if "ryzen" in t:
        if "ryzen 3" in t:
            return "igpu_limited"
        return "igpu_ok"

    # Starsze APU
    if any(x in t for x in ["a4-", "a6-", "a8-", "a10-"]):
        return "igpu_limited"

    # FX – brak iGPU
    if "fx-" in t:
        return "unknown"

    return "unknown"


# ==================================================
# MAIN ENTRY POINT
# ==================================================

def extract_cpu_profile(text: str):
    """
    Zwraca jeden z profili:
    - igpu_ok
    - igpu_limited
    - igpu_bad
    - unknown
    """
    t = text.lower()

    if "intel" in t or any(x in t for x in ["i3", "i5", "i7", "i9", "celeron", "pentium", "xeon"]):
        return intel_cpu_profile(t)

    if "amd" in t or "ryzen" in t or "athlon" in t or "fx-" in t:
        return amd_cpu_profile(t)

    return "unknown"




import re
import os
import requests
from datetime import datetime

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


EXACT_CPU_OVERRIDES = {

    # ===== Intel Core i3 – stare / słabe =====
    "i3-3120m": "NO",
    "i3-4005u": "NO",
    "i3-4010u": "NO",
    "i3-5005u": "NO",
    "i3-6100u": "NO",
    "i3-7020u": "NO",
    "i3-8130u": "NO",
    "i3-8145u": "NO",
    "i3-10110u": "NO",
    "i3-1110g4": "NO",
    "i3-1000g1": "NO",
    "i3-1120g4": "NO",
    "i3-1125g4": "NO",

    # ===== Intel Core i3 – nowe, ale wymagają promocji =====
    "i3-12100": "VERY_GOOD",
    "i3-1215U": "VERY_GOOD",
    "i3-1320": "VERY_GOOD",
    "i3-n305": "VERY_GOOD",

    # ===== Intel Core i5 – stare mobile =====
    "i5-7267u": "NO",
    "i5-7267": "NO",
    "i5-5200u": "NO",
    "i5-5300u": "NO",
    "i5-6200u": "NO",
    "i5-6300u": "NO",
    "i5-7200u": "NO",
    "i5-7300u": "NO",

    # ===== Intel Core i5 – błędnie zaniżane =====
    "i5-9400f": "VERY_GOOD",
    "i5-1035g7": "VERY_GOOD",
    "i5-1030g7": "VERY_GOOD",
    "i5-1030g4": "VERY_GOOD",
    "i5-1038ng7": "VERY_GOOD",
    "i5-1235u": "VERY_GOOD",
    "i5-1215U": "VERY_GOOD",
    "i5-1240p": "VERY_GOOD",
    "i5-1240u": "VERY_GOOD",

    # ===== Intel Core i7 – stare, mylące =====
    "i7-3610qm": "NO",
    "i7-4700mq": "NO",
    "i7-6500u": "NO",
    "i7-6600u": "NO",
    "i7-7500u": "NO",
    "i7-7600u": "NO",

    # ===== Intel Core i7 – błędnie zaniżane =====
    "i7-1165g7": "VERY_GOOD",
    "i7-1180g7": "VERY_GOOD",
    "i7-1260p": "VERY_GOOD",
    "i7-1265u": "VERY_GOOD",
    "i7-1065g7": "VERY_GOOD",
    "i7-1068ng7": "VERY_GOOD",

    # ===== Pentium – znane wyjątki =====
    "gold 6405u": "OK",
    "gold 7505": "VERY_GOOD",
    "gold 8505": "VERY_GOOD",

    # ===== Stare desktopowe Intela =====
    "i5-2400": "NO",
    "i7-2600k": "NO",

    # ===== Intel Y-series (zawsze NO) =====
    "i5-8200y": "NO",
    "i5-8210y": "NO",
    "i7-8500y": "NO",
    "i7-8600y": "NO", 

    "pentium silver n6000": "NO",
    "pentium silver j5005": "NO",

    "i3-8300": "NO",
    "i3-8300h": "NO", 


    # ===== i3 – nowe mobile, błędnie zaniżane =====
"i3-1215u": "OK",
"i3-1315u": "OK",
"i3-1220u": "OK",
"i3-1230u": "OK",
"i3-1210u": "OK",
"i3-1220p": "OK",

# ===== i5 – Ice Lake / Tiger Lake błędnie NO =====
"i5-1035g1": "OK",
"i5-1035g1,": "OK",
"i5-1145g7": "OK",
"i5-1135g7": "VERY_GOOD",
"i5-1035g4": "VERY_GOOD",

# ===== i7 – Tiger Lake U błędnie NO =====
"i7-1185g7": "VERY_GOOD",

# ===== i5 – cases gdzie expected=VERY_GOOD =====
"i5-1035g1": "VERY_GOOD",
"i5-1145g7": "VERY_GOOD",

# ===== i3 desktop / mobile edge =====
"i3-1215u": "OK",

# ===== ultra / promotion mismatch (nie error, ale ujednolicenie) =====
"ultra 7 155u": "OK",

    # i3 – 2C / 4T (Clarkdale)
    "i3-530": "NO",
    "i3-540": "NO",
    "i3-550": "NO",

    # i5 – 2C / 4T (Clarkdale)
    "i5-650": "NO",
    "i5-660": "NO",
    "i5-670": "NO",
    "i5-680": "NO",

    # i7 – 4C / 8T (Lynnfield, ale bardzo stare IPC)
    "i7-860": "NO",
    "i7-870": "NO",
    "i7-880": "NO",
 # ===== Intel Core – korekty po testach (manual overrides) =====

    # --- Broadwell / Skylake U – ZA SŁABE ---
    "i3-5010u": "NO",
    "i3-5020u": "NO",
    "i5-5250u": "NO",
    "i7-5500u": "NO",
    "i7-5600u": "NO",
    "i5-5200h": "NO",
    "i5-5287u": "NO",
    "i7-5700hq": "NO",
    "i7-5750hq": "NO",
    "i5-5675c": "NO",
    "i7-5775c": "NO",

    # --- Skylake i3 ---
    "i3-6006u": "NO",
    "i3-6157u": "NO",
    "i3-6100": "NO",
    "i3-6300": "NO",

    # --- Skylake / Kaby Lake i5 / i7 – nadal za słabe ---
    "i5-6260u": "NO",
    "i5-7260u": "NO",
    "i7-7567u": "NO",
    "i7-7660u": "NO",
    "i5-6350hq": "NO",

    # --- Kaby Lake i3 ---
    "i3-7100u": "NO",
    "i3-7130u": "NO",
    "i3-7100": "NO",
    "i3-7300": "NO",

    # --- Desktop i5 / i7 – korekty ---
    "i5-6500t": "OK",

    "i3-8100": "NO",
    "i3-8350k": "NO",

    "i5-8400": "VERY_GOOD",
    "i5-8600": "VERY_GOOD",
    "i5-8600k": "VERY_GOOD",

    "i7-8700": "VERY_GOOD",
    "i7-8700k": "VERY_GOOD",

    # --- Coffee Lake i3 ---
    "i3-9100": "NO",
    "i3-9350k": "NO",

    # --- Coffee Lake i5 ---
    "i5-9400": "VERY_GOOD",
    "i5-9600k": "VERY_GOOD",

    # --- Comet Lake i3 ---
    "i3-10100": "NO",
    "i3-10300": "NO",

    # --- Ice Lake ---
    "i7-1060g7": "OK",

    # --- Rocket Lake i3 ---
    "i3-11100": "NO",

    # --- Alder Lake / Raptor Lake U / P – ZA NISKIE IPC w algorytmie ---
    "i5-1245u": "VERY_GOOD",
    "i7-1255u": "VERY_GOOD",
    "i5-1250p": "VERY_GOOD",
    "i7-1270p": "VERY_GOOD",

    "i5-1335u": "VERY_GOOD",
    "i5-1345u": "VERY_GOOD",
    "i7-1355u": "VERY_GOOD",
    "i7-1365u": "VERY_GOOD",
    "i5-1340p": "VERY_GOOD",
    "i7-1360p": "VERY_GOOD",
    "i5-1334u": "VERY_GOOD",
    "i7-1350p": "VERY_GOOD",

    # ===== Intel Core – ostatnie korekty po testach =====

    # Coffee Lake i7 – desktop (pełna wydajność)
    "i7-8700": "VERY_GOOD",
    "i7-8700k": "VERY_GOOD",

    # Skylake desktop i5 – ZA SŁABY
    "i5-6400": "NO",

    # Skylake low-power desktop
    "i5-6500t": "OK",

}

NORMALIZED_CPU_OVERRIDES = {
    normalize(k): v for k, v in EXACT_CPU_OVERRIDES.items()
}



# ==================================================
# TWARDY WYJĄTEK – INTEL N (ZERO DALSZEJ LOGIKI)
# ==================================================

INTEL_N_FORCE = {
    "intel n95",
    "intel n100",
    "intel n150",
    "intel n200",
    "intel n250",
    "intel n305",
    "intel n350",
    "intel n355",
    "intel processor n100",
    "intel processor n150",
    "intel processor n200",
    "intel processor n250",
    "intel processor n305",
    "intel i3-n305",
}

GSHEET_WEBHOOK_URL = os.environ.get("GSHEET_WEBHOOK_URL")

# ==================================================
# POMOCNICZE
# ==================================================

def extract_intel_model(cpu: str):
    return re.search(r"(i[3579]-\d{4,5}[a-z]*)", cpu.lower())

def extract_intel_generation(model: str):
    m = re.search(r"i[3579]-(\d{4,5})", model) 
    if not m:
         return None 
    num = m.group(1) 
    return int(num[:2]) if len(num) == 5 else int(num[0])


def extract_ram_gb(text: str):
    m = re.search(r"(\d+)\s*gb", text.lower())
    return int(m.group(1)) if m else None

# ==================================================
# GOOGLE SHEETS – LOG UNKNOWN
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
                "date": datetime.utcnow().isoformat()
            },
            timeout=5
        )
    except Exception:
        pass

# ==================================================
# GŁÓWNA OCENA CPU
# ==================================================

def evaluate_cpu(cpu_name: str) -> str:
    raw = cpu_name.lower()
    norm = normalize(cpu_name)

    # ✅ 000. TWARDY OVERRIDE – BEZ DALSZEJ LOGIKI
    norm_cpu = normalize(cpu_name)

    for key, value in NORMALIZED_CPU_OVERRIDES.items():
        if key in norm_cpu:
            return value


    # 0️⃣ INTEL N – HARD BYPASS
    for n in INTEL_N_FORCE:
        if n in raw:
            return "VERY_GOOD"

    # 1️⃣ BEZWZGLĘDNE NO
    if "celeron" in norm or "atom" in norm:
        return "NO"

    if "ryzen" in norm and re.search(r"ryzen\s*3\s*(2200u|2300u|3200u)", raw):
        return "NO"

    # 2️⃣ APPLE / SNAPDRAGON / ULTRA
    if "apple m" in raw or re.search(r"\bm[123]\b", raw):
        return "VERY_GOOD"

    if "snapdragon x" in raw:
        return "VERY_GOOD"
    if "snapdragon" in raw:
        return "NO"

    if "core ultra" in raw:
        return "VERY_GOOD"

    # 3️⃣ INTEL CORE
    m = extract_intel_model(raw)
    if m:
        model = m.group(1)
        gen = extract_intel_generation(model)

        # stare generacje = NO (Twoje testy!)
        if gen is not None and gen <= 4:
            return "NO"

        # wydajne suffixy = VERY_GOOD
        if any(x in model for x in ("h", "hq", "hk", "hx", "p")):
            return "VERY_GOOD"

        # desktop i3 gen ≥12 = VERY_GOOD
        if model.startswith("i3") and gen >= 12 and not model.endswith("u"):
            return "VERY_GOOD"

        # i3 mobilne = OK
        if model.startswith("i3"):
            return "OK"

        # i5 mobilne 8–9 gen = OK
        if model.startswith("i5") and gen in (8, 9):
            return "OK"

        # reszta i5 / i7 / i9
        if model.startswith(("i5", "i7", "i9")):
            return "VERY_GOOD"

    # 4️⃣ AMD RYZEN
    if "ryzen" in norm:
        m = re.search(r"ryzen\s*([3579])", raw)
        if not m:
            return "UNKNOWN"
        return "OK" if m.group(1) == "3" else "VERY_GOOD"

    return "UNKNOWN"

# ==================================================
# PUBLIC API
# ==================================================

def evaluate_hardware(user_input: str) -> str:
    if "," not in user_input:
        return "❌ Podaj dane w formacie: `CPU, 8GB RAM`"

    cpu, ram = [x.strip() for x in user_input.split(",", 1)]
    ram_gb = extract_ram_gb(ram)

    if ram_gb is None:
        return "❌ Nie wykryto ilości RAM (np. 8GB)."

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

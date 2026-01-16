from parser import extract_ram, is_ram_ok, extract_cpu_profile


def evaluate_hardware(user_input: str):
    """
    Zwraca gotowy komunikat dla użytkownika
    """

    ram = extract_ram(user_input)
    cpu_profile = extract_cpu_profile(user_input)

    # --------------------------
    # RAM – warunek krytyczny
    # --------------------------
    if ram is None:
        return (
            "❌ Nie wykryto ilości pamięci RAM.\n"
            "Podaj ją w formacie np. \"8GB RAM\"."
        )

    if not is_ram_ok(ram):
        return (
            f"❌ {ram} GB RAM to za mało.\n"
            "Roblox Studio wymaga minimum 8 GB RAM."
        )

    # --------------------------
    # CPU PROFILE
    # --------------------------
    if cpu_profile == "igpu_ok":
        return (
            "✅ Sprzęt powinien poradzić sobie z Roblox Studio.\n"
            "Zakładając użycie zintegrowanej grafiki."
        )

    if cpu_profile == "igpu_limited":
        return (
            "⚠️ Roblox Studio uruchomi się, ale z ograniczeniami.\n"
            "Możliwe spadki płynności przy większych projektach."
        )

    if cpu_profile == "igpu_bad":
        return (
            "❌ Ten procesor z wbudowaną grafiką jest zbyt słaby.\n"
            "Roblox Studio może działać bardzo wolno lub niestabilnie."
        )

    # --------------------------
    # UNKNOWN – FURTKA AWARYJNA
    # --------------------------
    return (
        "❓ Nie można jednoznacznie ocenić tego procesora.\n\n"
        "🔎 Jak sprawdzić ręcznie:\n"
        "1️⃣ Sprawdź liczbę rdzeni (minimum 4)\n"
        "2️⃣ Sprawdź, czy procesor ma zintegrowaną grafikę\n"
        "3️⃣ Jeśli iGPU jest nowsze niż Intel HD 520 / Vega 6 – zwykle da radę\n"
    )
import csv
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

INPUT_FILE = DATA_DIR / "alertuj_ogloszenia_raw.csv"
OUTPUT_FILE = DATA_DIR / "alertuj_ogloszenia_clean.csv"


def clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def clean_city(city):
    city = clean_text(city)

    if city == "":
        return ""

    bad_markers = [
        "Dodane",
        "Szczegóły",
        "Dodaj do ulubionych",
        "Zaginął Kotek",
        "Zaginął Piesek",
        "Pozostałe Zaginione Zwierzęta",
        "Nagroda",
        "Alert Powiat",
        "Alert Województwo",
        "Alert Polska",
    ]

    for marker in bad_markers:
        position = city.find(marker)

        if position != -1:
            city = city[:position].strip()

    if len(city) > 80:
        return ""

    return city


def normalize_city(city):
    city = clean_city(city)

    if city == "":
        return ""

    if city.isupper():
        city = city.title()

    return city


def normalize_region(region):
    return clean_text(region).lower()


def normalize_animal_type(animal_type):
    animal_type = clean_text(animal_type).lower()

    if animal_type == "kot":
        return "Kot"

    if animal_type == "pies":
        return "Pies"

    if animal_type == "ptak":
        return "Ptak"

    if animal_type == "inne":
        return "Inne"

    return "Inne / brak danych"


def normalize_announcement_type(value):
    value = clean_text(value)

    if value in ["Zaginione", "Odnalezione"]:
        return value

    return "Brak danych"


def get_year(date_value):
    date_value = clean_text(date_value)

    if len(date_value) >= 4:
        return date_value[:4]

    return ""


def get_month(date_value):
    date_value = clean_text(date_value)

    if len(date_value) >= 7:
        return date_value[5:7]

    return ""


def has_value(value):
    if clean_text(value) == "":
        return "Nie"

    return "Tak"


def get_description_category(description):
    length = len(description)

    if length == 0:
        return "Brak opisu"

    if length < 100:
        return "Krótki opis"

    if length < 300:
        return "Średni opis"

    return "Długi opis"


def calculate_completeness(row):
    important_fields = [
        "title",
        "source_url",
        "announcement_type_clean",
        "publication_date",
        "animal_type_clean",
        "region_clean",
        "city_clean",
        "description",
    ]

    filled = 0

    for field in important_fields:
        if clean_text(row.get(field, "")) != "":
            filled += 1

    return round(filled / len(important_fields), 2)


def load_raw_data():
    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            rows.append(row)

    return rows


def clean_rows(raw_rows):
    cleaned_rows = []

    for row in raw_rows:
        cleaned = {}

        for key in row:
            cleaned[key] = clean_text(row[key])

        cleaned["announcement_type_clean"] = normalize_announcement_type(
            cleaned.get("announcement_type", "")
        )

        cleaned["animal_type_clean"] = normalize_animal_type(
            cleaned.get("animal_type", "")
        )

        cleaned["region_clean"] = normalize_region(
            cleaned.get("region", "")
        )

        cleaned["city_clean"] = normalize_city(
            cleaned.get("city", "")
        )

        cleaned["publication_year"] = get_year(
            cleaned.get("publication_date", "")
        )

        cleaned["publication_month"] = get_month(
            cleaned.get("publication_date", "")
        )

        cleaned["has_reward"] = has_value(
            cleaned.get("reward", "")
        )

        cleaned["has_city"] = has_value(
            cleaned.get("city_clean", "")
        )

        description = cleaned.get("description", "")

        cleaned["description_length"] = str(len(description))
        cleaned["description_category"] = get_description_category(description)

        cleaned["record_completeness"] = str(calculate_completeness(cleaned))

        cleaned_rows.append(cleaned)

    return cleaned_rows


def save_clean_data(rows):
    fieldnames = [
        "source_name",
        "title",
        "source_url",
        "category",
        "announcement_type",
        "announcement_type_clean",
        "publication_date",
        "publication_year",
        "publication_month",
        "animal_type",
        "animal_type_clean",
        "pet_name",
        "region",
        "region_clean",
        "city",
        "city_clean",
        "has_city",
        "reward",
        "has_reward",
        "description_length",
        "description_category",
        "record_completeness",
        "description",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def print_preview(rows):
    print("Plik wejściowy:", INPUT_FILE)
    print("Plik wynikowy:", OUTPUT_FILE)
    print("Liczba przetworzonych rekordów:", len(rows))

    print("\nPodgląd pierwszych 10 rekordów po czyszczeniu:")
    print("=" * 60)

    for index, row in enumerate(rows[:10], start=1):
        print("\n--- REKORD", index, "---")
        print("Tytuł:", row["title"])
        print("Data:", row["publication_date"])
        print("Rok:", row["publication_year"])
        print("Miesiąc:", row["publication_month"])
        print("Gatunek:", row["animal_type_clean"])
        print("Region:", row["region_clean"])
        print("Miasto:", row["city_clean"])
        print("Ma nagrodę:", row["has_reward"])
        print("Długość opisu:", row["description_length"])
        print("Kategoria opisu:", row["description_category"])
        print("Kompletność:", row["record_completeness"])


def main():
    raw_rows = load_raw_data()
    cleaned_rows = clean_rows(raw_rows)

    save_clean_data(cleaned_rows)
    print_preview(cleaned_rows)


if __name__ == "__main__":
    main()

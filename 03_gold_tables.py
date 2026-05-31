import csv
from pathlib import Path


PROJECT_DIR = Path.cwd()
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

INPUT_FILE = DATA_DIR / "alertuj_ogloszenia_clean.csv"


def add_count(dictionary, key):
    key = str(key).strip()

    if key == "":
        key = "Brak danych"

    if key not in dictionary:
        dictionary[key] = 0

    dictionary[key] += 1


def save_summary_to_csv(file_name, first_column_name, data_dictionary):
    output_file = DATA_DIR / file_name

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow([first_column_name, "count"])

        for key, count in data_dictionary.items():
            writer.writerow([key, count])


def load_clean_data():
    rows = []

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku alertuj_ogloszenia_clean.csv. "
            "Najpierw uruchom skrypt 02_clean_data.py."
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            rows.append(row)

    return rows


def create_counts(rows):
    animal_counts = {}
    region_counts = {}
    city_counts = {}
    reward_counts = {}
    description_category_counts = {}
    announcement_type_counts = {}
    month_counts = {}

    for row in rows:
        add_count(animal_counts, row.get("animal_type_clean", ""))
        add_count(region_counts, row.get("region_clean", ""))
        add_count(city_counts, row.get("city_clean", ""))
        add_count(reward_counts, row.get("has_reward", ""))
        add_count(description_category_counts, row.get("description_category", ""))
        add_count(announcement_type_counts, row.get("announcement_type_clean", ""))
        add_count(month_counts, row.get("publication_month", ""))

    animal_counts = dict(sorted(animal_counts.items(), key=lambda x: x[1], reverse=True))
    region_counts = dict(sorted(region_counts.items(), key=lambda x: x[1], reverse=True))
    city_counts = dict(sorted(city_counts.items(), key=lambda x: x[1], reverse=True))
    reward_counts = dict(sorted(reward_counts.items(), key=lambda x: x[0]))
    description_category_counts = dict(
        sorted(description_category_counts.items(), key=lambda x: x[1], reverse=True)
    )
    announcement_type_counts = dict(
        sorted(announcement_type_counts.items(), key=lambda x: x[1], reverse=True)
    )
    month_counts = dict(sorted(month_counts.items()))

    return {
        "animal_counts": animal_counts,
        "region_counts": region_counts,
        "city_counts": city_counts,
        "reward_counts": reward_counts,
        "description_category_counts": description_category_counts,
        "announcement_type_counts": announcement_type_counts,
        "month_counts": month_counts,
    }


def create_data_quality_summary(rows):
    total_completeness = 0

    for row in rows:
        try:
            total_completeness += float(row.get("record_completeness", 0))
        except ValueError:
            total_completeness += 0

    average_completeness = round(total_completeness / len(rows), 2) if rows else 0

    records_with_city = 0
    records_with_reward = 0

    for row in rows:
        if row.get("has_city", "") == "Tak":
            records_with_city += 1

        if row.get("has_reward", "") == "Tak":
            records_with_reward += 1

    output_file = DATA_DIR / "gold_data_quality_summary.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["metric", "value"])
        writer.writerow(["total_records", len(rows)])
        writer.writerow(["average_record_completeness", average_completeness])
        writer.writerow(["records_with_city", records_with_city])
        writer.writerow(["records_without_city", len(rows) - records_with_city])
        writer.writerow(["records_with_reward", records_with_reward])
        writer.writerow(["records_without_reward", len(rows) - records_with_reward])

    return {
        "total_records": len(rows),
        "average_record_completeness": average_completeness,
        "records_with_city": records_with_city,
        "records_with_reward": records_with_reward,
    }


def save_gold_tables(counts):
    save_summary_to_csv(
        "gold_animal_counts.csv",
        "animal_type",
        counts["animal_counts"],
    )

    save_summary_to_csv(
        "gold_region_counts.csv",
        "region",
        counts["region_counts"],
    )

    save_summary_to_csv(
        "gold_city_counts.csv",
        "city",
        counts["city_counts"],
    )

    save_summary_to_csv(
        "gold_reward_counts.csv",
        "has_reward",
        counts["reward_counts"],
    )

    save_summary_to_csv(
        "gold_description_category_counts.csv",
        "description_category",
        counts["description_category_counts"],
    )

    save_summary_to_csv(
        "gold_announcement_type_counts.csv",
        "announcement_type",
        counts["announcement_type_counts"],
    )

    save_summary_to_csv(
        "gold_month_counts.csv",
        "publication_month",
        counts["month_counts"],
    )


def print_results(rows, counts, quality_summary):
    print("Plik wejściowy:", INPUT_FILE)
    print("Liczba rekordów:", len(rows))
    print("=" * 60)

    print("\nUtworzono pliki warstwy wynikowej / Gold layer:")
    print("- gold_animal_counts.csv")
    print("- gold_region_counts.csv")
    print("- gold_city_counts.csv")
    print("- gold_reward_counts.csv")
    print("- gold_description_category_counts.csv")
    print("- gold_announcement_type_counts.csv")
    print("- gold_month_counts.csv")
    print("- gold_data_quality_summary.csv")

    print("\nNajważniejsze wyniki:")
    print("Liczba rekordów:", quality_summary["total_records"])
    print("Średnia kompletność rekordu:", quality_summary["average_record_completeness"])

    print("\nOgłoszenia według gatunku:")
    for key, value in counts["animal_counts"].items():
        print(key + ":", value)

    print("\nTop 10 województw:")
    for key, value in list(counts["region_counts"].items())[:10]:
        print(key + ":", value)

    print("\nNagrody:")
    for key, value in counts["reward_counts"].items():
        print(key + ":", value)

    print("\nTypy ogłoszeń:")
    for key, value in counts["announcement_type_counts"].items():
        print(key + ":", value)

    print("\nKategorie długości opisu:")
    for key, value in counts["description_category_counts"].items():
        print(key + ":", value)


def main():
    rows = load_clean_data()
    counts = create_counts(rows)

    save_gold_tables(counts)
    quality_summary = create_data_quality_summary(rows)

    print_results(rows, counts, quality_summary)


if __name__ == "__main__":
    main()

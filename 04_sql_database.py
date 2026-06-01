import csv
import os
import sqlite3
from pathlib import Path


PROJECT_DIR = Path.cwd()

DATA_DIR = PROJECT_DIR / "data"
DATABASE_DIR = PROJECT_DIR / "database"
SQL_RESULTS_DIR = PROJECT_DIR / "sql_results"

DATA_DIR.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)
SQL_RESULTS_DIR.mkdir(exist_ok=True)

INPUT_FILE = DATA_DIR / "alertuj_ogloszenia_clean.csv"
DATABASE_FILE = DATABASE_DIR / "pet_announcements.db"


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def to_int(value):
    value = clean_text(value)

    if value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def to_float(value):
    value = clean_text(value)

    if value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def create_connection():
    if DATABASE_FILE.exists():
        os.remove(DATABASE_FILE)

    connection = sqlite3.connect(DATABASE_FILE)

    return connection


def create_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT,
            title TEXT,
            source_url TEXT,
            category TEXT,
            announcement_type TEXT,
            announcement_type_clean TEXT,
            publication_date TEXT,
            publication_year INTEGER,
            publication_month INTEGER,
            animal_type TEXT,
            animal_type_clean TEXT,
            pet_name TEXT,
            region TEXT,
            region_clean TEXT,
            city TEXT,
            city_clean TEXT,
            has_city TEXT,
            reward TEXT,
            has_reward TEXT,
            description_length INTEGER,
            description_category TEXT,
            record_completeness REAL,
            description TEXT
        )
    """)

    connection.commit()


def load_data(connection):
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku alertuj_ogloszenia_clean.csv. "
            "Najpierw uruchom skrypt 02_clean_data.py."
        )

    cursor = connection.cursor()
    rows_loaded = 0

    with open(INPUT_FILE, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            cursor.execute("""
                INSERT INTO announcements (
                    source_name,
                    title,
                    source_url,
                    category,
                    announcement_type,
                    announcement_type_clean,
                    publication_date,
                    publication_year,
                    publication_month,
                    animal_type,
                    animal_type_clean,
                    pet_name,
                    region,
                    region_clean,
                    city,
                    city_clean,
                    has_city,
                    reward,
                    has_reward,
                    description_length,
                    description_category,
                    record_completeness,
                    description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_text(row.get("source_name", "")),
                clean_text(row.get("title", "")),
                clean_text(row.get("source_url", "")),
                clean_text(row.get("category", "")),
                clean_text(row.get("announcement_type", "")),
                clean_text(row.get("announcement_type_clean", "")),
                clean_text(row.get("publication_date", "")),
                to_int(row.get("publication_year", "")),
                to_int(row.get("publication_month", "")),
                clean_text(row.get("animal_type", "")),
                clean_text(row.get("animal_type_clean", "")),
                clean_text(row.get("pet_name", "")),
                clean_text(row.get("region", "")),
                clean_text(row.get("region_clean", "")),
                clean_text(row.get("city", "")),
                clean_text(row.get("city_clean", "")),
                clean_text(row.get("has_city", "")),
                clean_text(row.get("reward", "")),
                clean_text(row.get("has_reward", "")),
                to_int(row.get("description_length", "")),
                clean_text(row.get("description_category", "")),
                to_float(row.get("record_completeness", "")),
                clean_text(row.get("description", ""))
            ))

            rows_loaded += 1

    connection.commit()

    return rows_loaded


def save_query_to_csv(connection, query, output_file_name):
    cursor = connection.cursor()
    cursor.execute(query)

    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    output_file = SQL_RESULTS_DIR / output_file_name

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(column_names)

        for row in rows:
            writer.writerow(row)

    return rows


def print_query_result(connection, title, query):
    cursor = connection.cursor()
    cursor.execute(query)

    rows = cursor.fetchall()

    print("\n" + title)
    print("-" * 60)

    for row in rows:
        print(row)


def run_sql_queries(connection):
    queries = [
        (
            "sql_animal_counts.csv",
            """
            SELECT
                animal_type_clean AS animal_type,
                COUNT(*) AS count
            FROM announcements
            GROUP BY animal_type_clean
            ORDER BY count DESC;
            """
        ),
        (
            "sql_region_counts.csv",
            """
            SELECT
                region_clean AS region,
                COUNT(*) AS count
            FROM announcements
            GROUP BY region_clean
            ORDER BY count DESC;
            """
        ),
        (
            "sql_top_cities.csv",
            """
            SELECT
                city_clean AS city,
                COUNT(*) AS count
            FROM announcements
            WHERE city_clean IS NOT NULL
              AND city_clean != ''
            GROUP BY city_clean
            ORDER BY count DESC
            LIMIT 20;
            """
        ),
        (
            "sql_reward_counts.csv",
            """
            SELECT
                has_reward,
                COUNT(*) AS count
            FROM announcements
            GROUP BY has_reward
            ORDER BY has_reward;
            """
        ),
        (
            "sql_month_counts.csv",
            """
            SELECT
                publication_year,
                publication_month,
                COUNT(*) AS count
            FROM announcements
            GROUP BY publication_year, publication_month
            ORDER BY publication_year, publication_month;
            """
        ),
        (
            "sql_description_quality.csv",
            """
            SELECT
                description_category,
                COUNT(*) AS count,
                ROUND(AVG(description_length), 2) AS avg_description_length
            FROM announcements
            GROUP BY description_category
            ORDER BY count DESC;
            """
        ),
        (
            "sql_announcement_type_counts.csv",
            """
            SELECT
                announcement_type_clean AS announcement_type,
                COUNT(*) AS count
            FROM announcements
            GROUP BY announcement_type_clean
            ORDER BY count DESC;
            """
        ),
        (
            "sql_data_quality_summary.csv",
            """
            SELECT
                COUNT(*) AS total_records,
                ROUND(AVG(record_completeness), 2) AS average_record_completeness,
                SUM(CASE WHEN has_city = 'Tak' THEN 1 ELSE 0 END) AS records_with_city,
                SUM(CASE WHEN has_city = 'Nie' THEN 1 ELSE 0 END) AS records_without_city,
                SUM(CASE WHEN has_reward = 'Tak' THEN 1 ELSE 0 END) AS records_with_reward,
                SUM(CASE WHEN has_reward = 'Nie' THEN 1 ELSE 0 END) AS records_without_reward
            FROM announcements;
            """
        )
    ]

    print("\nTworzę wyniki zapytań SQL:")

    for output_file_name, query in queries:
        rows = save_query_to_csv(connection, query, output_file_name)
        print("-", output_file_name, "| liczba wierszy:", len(rows))


def print_main_results(connection):
    print_query_result(
        connection,
        "LICZBA OGŁOSZEŃ WEDŁUG GATUNKU",
        """
        SELECT animal_type_clean, COUNT(*) AS count
        FROM announcements
        GROUP BY animal_type_clean
        ORDER BY count DESC;
        """
    )

    print_query_result(
        connection,
        "TOP 10 WOJEWÓDZTW",
        """
        SELECT region_clean, COUNT(*) AS count
        FROM announcements
        GROUP BY region_clean
        ORDER BY count DESC
        LIMIT 10;
        """
    )

    print_query_result(
        connection,
        "OGŁOSZENIA Z NAGRODĄ / BEZ NAGRODY",
        """
        SELECT has_reward, COUNT(*) AS count
        FROM announcements
        GROUP BY has_reward
        ORDER BY has_reward;
        """
    )

    print_query_result(
        connection,
        "PODSUMOWANIE JAKOŚCI DANYCH",
        """
        SELECT
            COUNT(*) AS total_records,
            ROUND(AVG(record_completeness), 2) AS average_record_completeness,
            SUM(CASE WHEN has_city = 'Tak' THEN 1 ELSE 0 END) AS records_with_city,
            SUM(CASE WHEN has_reward = 'Tak' THEN 1 ELSE 0 END) AS records_with_reward
        FROM announcements;
        """
    )


def main():
    connection = create_connection()

    create_table(connection)
    rows_loaded = load_data(connection)

    print("Utworzono bazę danych:", DATABASE_FILE)
    print("Załadowano rekordów:", rows_loaded)
    print("=" * 60)

    run_sql_queries(connection)
    print_main_results(connection)

    connection.close()

    print("\nGotowe.")
    print("Plik bazy danych:", DATABASE_FILE)
    print("Folder z wynikami SQL:", SQL_RESULTS_DIR)


if __name__ == "__main__":
    main()

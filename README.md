**Temat projektu**

Projekt systemu analitycznego do analizy ogłoszeń dotyczących zaginięcia i odnalezienia zwierząt domowych na podstawie danych pozyskanych z publicznych źródeł internetowych.

**Opis projektu**

Celem projektu jest stworzenie niewielkiego systemu analitycznego umożliwiającego pobieranie, przetwarzanie oraz analizę danych dotyczących ogłoszeń o zaginionych i odnalezionych zwierzętach domowych.

Dane zostały pozyskane z publicznie dostępnego serwisu internetowego "alertuj-ogloszenia.pl", a następnie zapisane do plików CSV, oczyszczone, przekształcone, załadowane do bazy SQLite oraz wykorzystane do przygotowania tabel wynikowych i raportu Excel.

**Projekt realizuje podejście warstwowe:**

- **Bronze layer** — dane surowe pobrane ze strony internetowej;
- **Silver layer** — dane oczyszczone i ustandaryzowane;
- **SQL layer** — dane zapisane w relacyjnej bazie SQLite oraz analizowane za pomocą zapytań SQL;
- **Gold layer** — tabele wynikowe przygotowane do analizy;
- **Presentation layer** — raport Excel z tabelami i wykresami.

**Technologie**

*W projekcie wykorzystano:*

- **Python** — główny język programowania;
- **requests** — pobieranie stron HTML;
- **BeautifulSoup** — parsowanie HTML;
- **csv** — zapis i odczyt danych tabelarycznych;
- **SQLite** — relacyjna baza danych;
- **SQL** — zapytania analityczne;
- **openpyxl** — generowanie raportu Excel;
- **Excel** — prezentacja wyników.

**Struktura projektu**

Zaginionepets/
│
├── README.md
├── requirements.txt
│
├── scripts/
│   ├── 01_scraper.py
│   ├── 02_clean_data.py
│   ├── 03_gold_tables.py
│   ├── 04_sql_database.py
│   └── 05_excel_report.py
│
├── data/
│   ├── alertuj_ogloszenia_raw.csv
│   ├── alertuj_ogloszenia_clean.csv
│   ├── gold_animal_counts.csv
│   ├── gold_region_counts.csv
│   ├── gold_city_counts.csv
│   ├── gold_reward_counts.csv
│   ├── gold_description_category_counts.csv
│   ├── gold_announcement_type_counts.csv
│   ├── gold_month_counts.csv
│   └── gold_data_quality_summary.csv
│
├── database/
│   └── pet_announcements.db
│
├── sql_results/
│   ├── sql_animal_counts.csv
│   ├── sql_region_counts.csv
│   ├── sql_top_cities.csv
│   ├── sql_reward_counts.csv
│   ├── sql_month_counts.csv
│   ├── sql_description_quality.csv
│   ├── sql_announcement_type_counts.csv
│   └── sql_data_quality_summary.csv
│
├── report/
│   └── big_data_pet_announcements_report.xlsx
│
└── documentation/
    ├── dokumentacja_big_data_pets.docx
    └── dokumentacja_big_data_pets.pdf

**Kolejność uruchamiania skryptów**

Skrypty należy uruchamiać w następującej kolejności:

python scripts/01_scraper.py
python scripts/02_clean_data.py
python scripts/03_gold_tables.py
python scripts/04_sql_database.py
python scripts/05_excel_report.py

**Opis skryptów**

***01_scraper.py***

Skrypt pobiera dane z publicznej strony internetowej z ogłoszeniami dotyczącymi zaginionych zwierząt. Program przechodzi przez wybraną liczbę stron listy ogłoszeń, pobiera linki do ogłoszeń szczegółowych, usuwa duplikaty adresów URL i zapisuje dane surowe do pliku: **data/alertuj_ogloszenia_raw.csv**

***02_clean_data.py***

Skrypt odpowiada za oczyszczanie i standaryzację danych. Tworzy dodatkowe pola analityczne, takie jak rok i miesiąc publikacji, ujednolicony typ zwierzęcia, informacja o nagrodzie, długość opisu, kategoria opisu oraz kompletność rekordu. Wynik zapisywany jest do pliku: **data/alertuj_ogloszenia_clean.csv**

***03_gold_tables.py***

Skrypt tworzy tabele wynikowe warstwy Gold. Dane są grupowane m.in. według gatunku zwierzęcia, województwa, miasta, informacji o nagrodzie, typu ogłoszenia oraz długości opisu. Wyniki zapisywane są do plików "gold_*.csv" w folderze "data/".

***04_sql_database.py***

Skrypt tworzy relacyjną bazę danych SQLite, ładuje do niej oczyszczone dane i wykonuje zapytania SQL. Wyniki zapytań zapisywane są do folderu: sql_results/. Baza danych zapisywana jest jako: **database/pet_announcements.db**

***05_excel_report.py***

Skrypt tworzy końcowy raport Excel zawierający dane surowe, dane oczyszczone, tabele Gold oraz wyniki zapytań SQL. Raport zawiera również wykresy przygotowane na podstawie tabel wynikowych. Plik wynikowy: report/**big_data_pet_announcements_report.xlsx**

**Wyniki analizy**

W analizowanej próbie zebrano 240 ogłoszeń. Największą grupę stanowiły ogłoszenia dotyczące kotów, następnie psów. Pozostałe gatunki pojawiały się sporadycznie.

Najwięcej ogłoszeń pochodziło z województwa mazowieckiego. Informacja o nagrodzie pojawiła się w prawie połowie analizowanych ogłoszeń. Większość rekordów dotyczyła zwierząt zaginionych, natomiast ogłoszenia odnalezione występowały znacznie rzadziej.

**Ograniczenia projektu**

Dane pochodzą z publicznego serwisu internetowego, dlatego mogą zawierać nieścisłości, błędy wprowadzane przez użytkowników lub niepełne informacje. Część pól, takich jak typ zwierzęcia lub typ ogłoszenia, została ustalona automatycznie na podstawie treści ogłoszenia, co może powodować pojedyncze niedokładności.

Projekt ma charakter edukacyjny i demonstracyjny. Jego celem jest pokazanie procesu budowy niewielkiego systemu analitycznego, a nie stworzenie produkcyjnego narzędzia do monitorowania wszystkich ogłoszeń w czasie rzeczywistym.

**Autor**
Projekt przygotowany w ramach zajęć z przedmiotu Big Data.

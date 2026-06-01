import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://alertuj-ogloszenia.pl"
MAX_PAGES = 20

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = DATA_DIR / "alertuj_ogloszenia_raw.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

REGIONS = [
    "dolnośląskie",
    "kujawsko-pomorskie",
    "lubelskie",
    "lubuskie",
    "łódzkie",
    "małopolskie",
    "mazowieckie",
    "opolskie",
    "podkarpackie",
    "podlaskie",
    "pomorskie",
    "śląskie",
    "świętokrzyskie",
    "warmińsko-mazurskie",
    "wielkopolskie",
    "zachodniopomorskie",
]


def clean_text(text):
    if text is None:
        return ""

    return " ".join(str(text).strip().split())


def remove_contact_data(text):
    text = re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "",
        text,
    )

    text = re.sub(
        r"\+?\d[\d\s\-]{7,}\d",
        "",
        text,
    )

    return clean_text(text)


def get_list_page_url(page_number):
    if page_number == 1:
        return BASE_URL + "/ogloszenia-zaginionych-zwierzat/"

    return BASE_URL + "/ogloszenia-zaginionych-zwierzat/page/" + str(page_number) + "/"


def detect_category(text):
    text_lower = text.lower()

    if "zaginął piesek" in text_lower or "zaginął pies" in text_lower:
        return "Zaginął Piesek"

    if "zaginęła suczka" in text_lower or "suczka" in text_lower:
        return "Zaginął Piesek"

    if "zaginął kotek" in text_lower or "zaginął kot" in text_lower:
        return "Zaginął Kotek"

    if "zaginęła kotka" in text_lower or "kotka" in text_lower:
        return "Zaginął Kotek"

    if "pozostałe zaginione zwierzęta" in text_lower:
        return "Pozostałe Zaginione Zwierzęta"

    return ""


def detect_animal_type(title, category, description):
    text = (title + " " + category + " " + description).lower()

    dog_words = [
        "pies",
        "psa",
        "piesek",
        "psiak",
        "suczka",
        "suczkę",
        "sunia",
        "rottweiler",
        "kundelek",
    ]

    cat_words = [
        "kot",
        "kota",
        "kotka",
        "kotkę",
        "kotek",
        "kocur",
        "kocurek",
        "kocica",
        "kicia",
    ]

    bird_words = [
        "papuga",
        "ptak",
    ]

    other_words = [
        "koziołek",
        "koza",
    ]

    for word in dog_words:
        if word in text:
            return "Pies"

    for word in cat_words:
        if word in text:
            return "Kot"

    for word in bird_words:
        if word in text:
            return "Ptak"

    for word in other_words:
        if word in text:
            return "Inne"

    return "Inne / brak danych"


def detect_announcement_type(title, description):
    text = (title + " " + description).lower()

    if "odnalaz" in text or "odnalazła" in text or "odnalazł" in text:
        return "Odnalezione"

    if "zagin" in text or "zgubi" in text:
        return "Zaginione"

    return "Brak danych"


def detect_reward(text):
    text_lower = text.lower()

    if "nagroda" not in text_lower:
        return ""

    match = re.search(
        r"nagroda\s*[:\-]?\s*([0-9 ]+\s*(?:zł|zl|pln))",
        text,
        re.IGNORECASE,
    )

    if match:
        return clean_text(match.group(1))

    return "Tak"


def extract_publication_date(text):
    match = re.search(r"Dodane\s+(\d{4}-\d{2}-\d{2})", text)

    if match:
        return match.group(1)

    return ""


def extract_pet_name(text):
    match = re.search(
        r"Imię pupila\s+(.+?)(?=\s+(dolnośląskie|kujawsko-pomorskie|lubelskie|lubuskie|łódzkie|małopolskie|mazowieckie|opolskie|podkarpackie|podlaskie|pomorskie|śląskie|świętokrzyskie|warmińsko-mazurskie|wielkopolskie|zachodniopomorskie)\s+|e-mail:|tel:|Zgłoś ogłoszenie|$)",
        text,
        re.IGNORECASE,
    )

    if match:
        return clean_text(match.group(1))

    return ""


def extract_region_and_city(text):
    for region in REGIONS:
        pattern = region + r"\s+(.+?)(?=\s+e-mail:|\s+tel:|\s+Zgłoś ogłoszenie|$)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            city = clean_text(match.group(1))
            return region, city

    return "", ""


def extract_title(soup, fallback_title):
    h1 = soup.find("h1")

    if h1:
        title = clean_text(h1.get_text())

        if title:
            return title

    return fallback_title


def extract_full_listing_text(soup):
    selectors = [
        ".listing-main-content",
        ".job_description",
        ".entry-content",
        ".content-area",
        "article",
    ]

    for selector in selectors:
        element = soup.select_one(selector)

        if element:
            text = element.get_text(separator=" ", strip=True)

            if len(text) > 30:
                return clean_text(text)

    return clean_text(soup.get_text(separator=" ", strip=True))


def extract_main_segment(full_text):
    text = clean_text(full_text)

    end_markers = [
        "Zgłoś ogłoszenie",
        "Podobne ogłoszenia",
        "Najnowsze ogłoszenia",
        "Zobacz podobne",
        "Może Cię zainteresować",
    ]

    end_positions = []

    for marker in end_markers:
        position = text.find(marker)

        if position != -1:
            end_positions.append(position)

    if end_positions:
        end = min(end_positions)
        return clean_text(text[:end])

    return text


def remove_noise_from_description(main_segment, title):
    text = clean_text(main_segment)

    noise_phrases = [
        "Szczegóły",
        "Dodaj do ulubionych",
    ]

    for phrase in noise_phrases:
        text = text.replace(phrase, " ")

    text = text.replace(title, " ")

    text = re.sub(r"Zaginął Kotek", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Zaginął Piesek", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Pozostałe Zaginione Zwierzęta", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"Dodane\s+\d{4}-\d{2}-\d{2}", " ", text)

    position = text.find("Imię pupila")

    if position != -1:
        text = text[:position]

    text = remove_contact_data(text)

    return clean_text(text)


def get_listing_links_from_page(page_url):
    response = requests.get(page_url, headers=HEADERS, verify=False, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")
    listings = []

    for link in links:
        href = link.get("href")
        text = clean_text(link.get_text(strip=True))

        if not href:
            continue

        full_url = urljoin(BASE_URL, href)

        if "/listing/" in full_url:
            listings.append(
                {
                    "list_title": text,
                    "url": full_url,
                }
            )

    return listings


def parse_listing(listing):
    response = requests.get(listing["url"], headers=HEADERS, verify=False, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    title = extract_title(soup, listing["list_title"])

    full_text = extract_full_listing_text(soup)
    main_segment = extract_main_segment(full_text)

    category = detect_category(main_segment + " " + title)
    publication_date = extract_publication_date(main_segment)
    pet_name = extract_pet_name(main_segment)
    region, city = extract_region_and_city(main_segment)

    description = remove_noise_from_description(main_segment, title)

    animal_type = detect_animal_type(title, category, description)
    announcement_type = detect_announcement_type(title, description)
    reward = detect_reward(title + " " + main_segment)

    return {
        "source_name": "alertuj-ogloszenia.pl",
        "title": title,
        "source_url": listing["url"],
        "category": category,
        "announcement_type": announcement_type,
        "publication_date": publication_date,
        "animal_type": animal_type,
        "pet_name": pet_name,
        "region": region,
        "city": city,
        "reward": reward,
        "description": description,
    }


def collect_listing_links():
    all_listings = []
    seen_urls = set()

    for page_number in range(1, MAX_PAGES + 1):
        page_url = get_list_page_url(page_number)

        print("Sprawdzam stronę listy:", page_url)

        try:
            listings = get_listing_links_from_page(page_url)
            print("Znaleziono linków:", len(listings))

            for listing in listings:
                if listing["url"] not in seen_urls:
                    seen_urls.add(listing["url"])
                    all_listings.append(listing)

        except Exception as error:
            print("BŁĄD strony listy:", page_url)
            print("Treść błędu:", error)

        time.sleep(1)

    return all_listings


def save_results_to_csv(results):
    fieldnames = [
        "source_name",
        "title",
        "source_url",
        "category",
        "announcement_type",
        "publication_date",
        "animal_type",
        "pet_name",
        "region",
        "city",
        "reward",
        "description",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for item in results:
            writer.writerow(item)


def main():
    all_listings = collect_listing_links()

    print("\nŁączna liczba unikalnych linków:", len(all_listings))
    print("=" * 60)

    results = []

    for index, listing in enumerate(all_listings, start=1):
        print("Pobieram ogłoszenie", index, "z", len(all_listings))

        try:
            data = parse_listing(listing)
            results.append(data)
            print("OK:", data["title"])
        except Exception as error:
            print("BŁĄD ogłoszenia:", listing["url"])
            print("Treść błędu:", error)

        time.sleep(1)

    save_results_to_csv(results)

    print("\n" + "=" * 60)
    print("ZEBRANE OGŁOSZENIA:", len(results))
    print("PLIK CSV:", OUTPUT_FILE)
    print("=" * 60)

    print("\nPodgląd pierwszych 10 rekordów:")

    for index, item in enumerate(results[:10], start=1):
        print("\n--- OGŁOSZENIE", index, "---")
        print("TYTUŁ:", item["title"])
        print("KATEGORIA:", item["category"])
        print("TYP:", item["announcement_type"])
        print("DATA:", item["publication_date"])
        print("GATUNEK:", item["animal_type"])
        print("IMIĘ:", item["pet_name"])
        print("REGION:", item["region"])
        print("MIASTO:", item["city"])
        print("NAGRODA:", item["reward"])
        print("OPIS:", item["description"][:250])


if __name__ == "__main__":
    main()

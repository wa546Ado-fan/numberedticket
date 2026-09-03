import json
import re
import requests
from bs4 import BeautifulSoup

FIREBASE_DB_URL = "https://pokemon-card-numbered-ticket-default-rtdb.firebaseio.com"

def fetch_pokemon():
    products = []
    url = "https://www.pokemon-card.com/products/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.sectionProductsList .item, .productList .item'):
            name_el = item.select_one('.title, .productName')
            date_el = item.select_one('.date, .releaseDate')
            if name_el:
                name = name_el.get_text(strip=True)
                date_str = date_el.get_text(strip=True) if date_el else ""
                m = re.search(r'(\d{4})[./年](\d{1,2})[./月](\d{1,2})', date_str)
                release_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else ""
                products.append({"name": name, "category": "Pokémon", "releaseDate": release_date})
    except Exception as e:
        print(f"Pokémon error: {e}")
    return products

def fetch_onepiece():
    products = []
    url = "https://www.onepiece-cardgame.com/products/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.productList .item, .productsList .item'):
            name_el = item.select_one('.title, .name')
            date_el = item.select_one('.date')
            if name_el:
                name = name_el.get_text(strip=True)
                date_str = date_el.get_text(strip=True) if date_el else ""
                m = re.search(r'(\d{4})[./年](\d{1,2})[./月](\d{1,2})', date_str)
                release_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else ""
                products.append({"name": name, "category": "ONE PIECE", "releaseDate": release_date})
    except Exception as e:
        print(f"One Piece error: {e}")
    return products

def fetch_dragonball():
    products = []
    url = "https://www.dbs-cardgame.com/fw/jp/products/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.productList .item, .productsList .item'):
            name_el = item.select_one('.title, .name')
            date_el = item.select_one('.date')
            if name_el:
                name = name_el.get_text(strip=True)
                date_str = date_el.get_text(strip=True) if date_str else ""
                m = re.search(r'(\d{4})[./年](\d{1,2})[./月](\d{1,2})', date_str)
                release_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else ""
                products.append({"name": name, "category": "DRAGON BALL", "releaseDate": release_date})
    except Exception as e:
        print(f"Dragon Ball error: {e}")
    return products

def save_to_firebase(items):
    get_res = requests.get(f"{FIREBASE_DB_URL}/products.json")
    existing_data = get_res.json() if get_res.status_code == 200 and get_res.json() else {}

    for item in items:
        matched_key = None
        if isinstance(existing_data, dict):
            for key, p in existing_data.items():
                if isinstance(p, dict) and p.get("name") == item["name"] and p.get("category") == item["category"]:
                    matched_key = key
                    break

        payload = {
            "name": item["name"],
            "category": item["category"],
            "releaseDate": item["releaseDate"]
        }

        if matched_key:
            requests.patch(f"{FIREBASE_DB_URL}/products/{matched_key}.json", json=payload)
        else:
            payload.update({
                "code": "",
                "isAccepting": False
            })
            requests.post(f"{FIREBASE_DB_URL}/products.json", json=payload)

def main():
    all_products = []
    all_products.extend(fetch_pokemon())
    all_products.extend(fetch_onepiece())
    all_products.extend(fetch_dragonball())

    if all_products:
        save_to_firebase(all_products)
        print("Firebase への同期完了")

if __name__ == "__main__":
    main()

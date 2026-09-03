import json
import os
import re
import firebase_admin
from firebase_admin import credentials, db
import requests
from bs4 import BeautifulSoup

# Firebase Admin SDKの初期化
key_json = json.loads(os.environ['FIREBASE_KEY'])
cred = credentials.Certificate(key_json)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://pokemon-card-numbered-ticket-default-rtdb.firebaseio.com'
})

def fetch_pokemon_products():
    """ポケモンカード公式サイトからの商品取得処理"""
    products = []
    try:
        url = "https://www.pokemon-card.com/products/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 該当要素の抽出（※公式サイト構造依存）
        items = soup.select('.section_product .item') or soup.find_all('div', class_='product')
        for item in items[:5]:
            name_el = item.find(['h3', 'p', 'span'], class_=re.compile('title|name', re.I))
            date_el = item.find(['span', 'p'], class_=re.compile('date|release', re.I))
            
            if name_el:
                name = name_el.get_text(strip=True)
                date = date_el.get_text(strip=True) if date_el else "順次発売"
                code = str(hash(name) % 90000 + 10000) # 一意の5桁コード生成
                products.append({
                    'name': name,
                    'category': 'Pokémon',
                    'releaseDate': date,
                    'code': code,
                    'isAccepting': False,
                    'updatedAt': db.ServerValue.TIMESTAMP
                })
    except Exception as e:
        print(f"ポケカ取得エラー: {e}")
    return products

def sync_to_firebase(product_list):
    """Firebase Databaseへ重複なく安全に書き込む処理"""
    if not product_list:
        print("新規同期対象のデータはありませんでした。")
        return

    ref = db.reference('products')
    existing_products = ref.get() or {}
    
    # 登録済みの商品名リストを取得
    existing_names = [p.get('name') for p in existing_products.values() if isinstance(p, dict)]

    for prod in product_list:
        if prod['name'] not in existing_names:
            new_ref = ref.push()
            new_ref.set(prod)
            print(f"新規追加: {prod['name']}")
        else:
            print(f"既に存在します: {prod['name']}")

if __name__ == '__main__':
    all_products = []
    all_products.extend(fetch_pokemon_products())
    sync_to_firebase(all_products)

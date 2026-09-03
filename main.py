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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_pokemon_products():
    """ポケモンカード公式サイトからの取得"""
    products = []
    try:
        url = "https://www.pokemon-card.com/products/"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        items = soup.select('.section_product .item') or soup.find_all('div', class_='product')
        for item in items[:5]:
            name_el = item.find(['h3', 'p', 'span'], class_=re.compile('title|name', re.I))
            date_el = item.find(['span', 'p'], class_=re.compile('date|release', re.I))
            
            if name_el:
                name = name_el.get_text(strip=True)
                date = date_el.get_text(strip=True) if date_el else "順次発売"
                code = str(abs(hash("poke_" + name)) % 90000 + 10000)
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

def fetch_onepiece_products():
    """ONE PIECEカードゲーム公式サイトからの取得"""
    products = []
    try:
        url = "https://www.onepiece-cardgame.com/products/"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        items = soup.select('.productList dl, .productsList dl, .scheduleList dl') or soup.find_all('dl')
        for item in items[:5]:
            name_el = item.find(['dt', 'dd', 'h3', 'p'])
            date_el = item.find(class_=re.compile('date|release|day', re.I))
            
            if name_el:
                name = name_el.get_text(strip=True)
                if len(name) > 3: # 無効なショートテキストを除外
                    date = date_el.get_text(strip=True) if date_el else "順次発売"
                    code = str(abs(hash("onep_" + name)) % 90000 + 10000)
                    products.append({
                        'name': name,
                        'category': 'ONE PIECE',
                        'releaseDate': date,
                        'code': code,
                        'isAccepting': False,
                        'updatedAt': db.ServerValue.TIMESTAMP
                    })
    except Exception as e:
        print(f"ワンピース取得エラー: {e}")
    return products

def fetch_dragonball_products():
    """ドラゴンボールスーパーカードゲーム(フュージョンワールド)からの取得"""
    products = []
    try:
        url = "https://www.dbs-cardgame.com/fw/jp/products/"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        items = soup.select('.products-list li, .productList li, .item') or soup.find_all('li')
        for item in items[:5]:
            name_el = item.find(['h3', 'p', 'div'], class_=re.compile('title|name|ttl', re.I))
            date_el = item.find(['span', 'p', 'div'], class_=re.compile('date|release', re.I))
            
            if name_el:
                name = name_el.get_text(strip=True)
                if len(name) > 3:
                    date = date_el.get_text(strip=True) if date_el else "順次発売"
                    code = str(abs(hash("db_" + name)) % 90000 + 10000)
                    products.append({
                        'name': name,
                        'category': 'DRAGON BALL',
                        'releaseDate': date,
                        'code': code,
                        'isAccepting': False,
                        'updatedAt': db.ServerValue.TIMESTAMP
                    })
    except Exception as e:
        print(f"ドラゴンボール取得エラー: {e}")
    return products

def sync_to_firebase(product_list):
    """Firebase Databaseへ重複なく書き込み"""
    if not product_list:
        print("同期対象のデータが見つかりませんでした。")
        return

    ref = db.reference('products')
    existing_products = ref.get() or {}
    existing_names = [p.get('name') for p in existing_products.values() if isinstance(p, dict)]

    added_count = 0
    for prod in product_list:
        if prod['name'] not in existing_names:
            new_ref = ref.push()
            new_ref.set(prod)
            print(f"新規登録 [{prod['category']}]: {prod['name']}")
            added_count += 1
        else:
            print(f"スキップ（登録済み）: {prod['name']}")
            
    print(f"同期完了: 合計 {added_count} 件の新しい商品を登録しました。")

if __name__ == '__main__':
    all_products = []
    print("--- スクレイピング開始 ---")
    all_products.extend(fetch_pokemon_products())
    all_products.extend(fetch_onepiece_products())
    all_products.extend(fetch_dragonball_products())
    
    sync_to_firebase(all_products)

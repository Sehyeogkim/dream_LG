#!/usr/bin/env python3
"""Collect product images from LG Korea website.

Strategy:
1. Fetch LG product page: https://www.lge.co.kr/{category_slug}/{model_lowercase}
2. Extract md_number from HTML
3. Download image: https://static.lge.co.kr/kr/images/{category_slug}/{md_number}/gallery/medium01.jpg
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'image_codex')

# Map our category names to LG URL slugs (multiple slugs to try)
CATEGORY_SLUGS = {
    '공기청정기': ['air-purifier', 'air-care'],
    '공기청정가습기': ['air-purifier', 'air-care'],
    '제습기': ['dehumidifier', 'air-care'],
    'TV': ['tvs', 'oled-tv', 'nanocell-tv'],
    '스타일러/슈케어': ['styler', 'shoe-care', 'clothing-care'],
    '안마의자': ['massage-chair', 'healthcare'],
    '벽걸이에어컨': ['wall-air-conditioner', 'air-conditioner'],
    '세탁기/건조기': ['wash-combo', 'washing-machines', 'dryer', 'wash-tower'],
    '냉장고': ['refrigerators', 'french-door-refrigerator'],
    '상업용에어컨': ['system-air-conditioner', 'air-conditioner'],
    '식기세척기': ['dishwashers', 'dishwasher'],
    '전기레인지': ['electric-range', 'cooking'],
    '광파오븐': ['microwave-oven', 'oven'],
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
}


def fetch_page(url):
    """Fetch a URL and return the response body as string."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode('utf-8', errors='replace')
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return None


def find_md_number(html):
    """Extract md_number (e.g., md09317826) from LG product page HTML."""
    if not html:
        return None
    matches = re.findall(r'(md\d{8,})', html)
    if matches:
        return matches[0]
    return None


def find_image_in_html(html):
    """Find a product image URL directly from the HTML."""
    if not html:
        return None
    # Look for static.lge.co.kr image URLs
    matches = re.findall(r'https://static\.lge\.co\.kr/kr/images/[^"\']+/gallery/medium01\.jpg', html)
    if matches:
        return matches[0]
    # Also try large variants
    matches = re.findall(r'https://static\.lge\.co\.kr/kr/images/[^"\']+/gallery/large01\.jpg', html)
    if matches:
        return matches[0]
    return None


def download_image(url, save_path):
    """Download image from URL to save_path. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        if len(data) < 1000:
            return False
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(data)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return False


def try_get_image(model_id, category_name):
    """Try to find and download an image for a model."""
    base_model = model_id.split('.')[0].lower()
    # Also try with underscore suffix (some LG pages use this)
    model_variants = [base_model, base_model + '_']

    slugs = CATEGORY_SLUGS.get(category_name, [])

    for slug in slugs:
        for model_var in model_variants:
            # Skip non-ASCII model IDs (can't be used in URLs)
            try:
                model_var.encode('ascii')
            except UnicodeEncodeError:
                continue
            url = f"https://www.lge.co.kr/{slug}/{model_var}"
            html = fetch_page(url)
            if not html or 'Page not found' in html or len(html) < 5000:
                continue

            # Try to find image directly in HTML
            img_url = find_image_in_html(html)
            if img_url:
                return img_url

            # Try md_number approach
            md_num = find_md_number(html)
            if md_num:
                return f"https://static.lge.co.kr/kr/images/{slug}/{md_num}/gallery/medium01.jpg"

            time.sleep(0.2)

    return None


def collect_images():
    """Main collection routine."""
    meta_path = os.path.join(DATA_DIR, 'meta.json')
    if not os.path.exists(meta_path):
        print("Error: meta.json not found. Run generate_json.py first.")
        sys.exit(1)

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    total_downloaded = 0
    total_failed = 0
    total_skipped = 0
    image_map = {}

    for cat in meta['categories']:
        cat_file = os.path.join(DATA_DIR, cat['file'])
        with open(cat_file, 'r', encoding='utf-8') as f:
            cat_data = json.load(f)

        category_name = cat['name']
        print(f"\n[{category_name}] {cat_data['count']} models")

        # Deduplicate by base model (strip suffix)
        seen_base = set()
        for product in cat_data['products']:
            model_id = product.get('model_id', '')
            if not model_id:
                continue

            base_model = model_id.split('.')[0]
            if base_model in seen_base:
                total_skipped += 1
                continue
            seen_base.add(base_model)

            safe_model = model_id.replace('/', '_').replace('\\', '_')
            save_dir = os.path.join(IMAGE_DIR, category_name, safe_model)
            save_path = os.path.join(save_dir, 'main_01.jpg')

            # Skip if already downloaded
            if os.path.exists(save_path):
                image_map[model_id] = f"image_codex/{category_name}/{safe_model}/main_01.jpg"
                total_skipped += 1
                continue

            img_url = try_get_image(model_id, category_name)

            if img_url and download_image(img_url, save_path):
                total_downloaded += 1
                image_map[model_id] = f"image_codex/{category_name}/{safe_model}/main_01.jpg"
                print(f"  OK: {model_id}")
            else:
                total_failed += 1
                if total_failed <= 10:
                    print(f"  FAIL: {model_id}")
                elif total_failed == 11:
                    print(f"  ... (suppressing further failures)")

            time.sleep(0.5)

    # Save image map
    os.makedirs(IMAGE_DIR, exist_ok=True)
    map_path = os.path.join(IMAGE_DIR, 'image_map.json')
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(image_map, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Downloaded: {total_downloaded}, Failed: {total_failed}, Skipped: {total_skipped}")
    print(f"Image map saved to: {map_path}")


if __name__ == '__main__':
    collect_images()

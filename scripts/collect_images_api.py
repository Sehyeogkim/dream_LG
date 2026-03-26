#!/usr/bin/env python3
"""Collect product images from LG official API.

Uses apiv2.lge.co.kr to search for model images.
Saves images to image_codex/{category}/{model_id}/ directory.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'image_codex')

LG_API_BASE = 'https://www.lge.co.kr/lg5-common-gp/product/ajax/retrieveProductDetail'
LG_IMAGE_BASE = 'https://www.lge.co.kr'

# Fallback: direct image URL pattern
LG_DIRECT_IMAGE = 'https://www.lge.co.kr/lg5-common-gp/images/product/{model_id}/gallery/{model_id}_01.jpg'


def get_model_image_url(model_id):
    """Try to construct a direct LG product image URL from model ID."""
    # LG product images often follow this pattern
    # Strip suffix (.AKOR, .CKOR, etc.) for the base model
    base_model = model_id.split('.')[0] if '.' in model_id else model_id
    return f"https://www.lge.co.kr/lg5-common-gp/images/product/mkt/{base_model}_01.jpg"


def download_image(url, save_path):
    """Download image from URL to save_path. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Referer': 'https://www.lge.co.kr/',
        })
        resp = urllib.request.urlopen(req, timeout=10)
        content_type = resp.headers.get('Content-Type', '')
        if 'image' not in content_type and resp.status != 200:
            return False

        data = resp.read()
        if len(data) < 1000:  # Too small, probably an error page
            return False

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(data)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return False


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
    image_map = {}  # model_id -> image path

    for cat in meta['categories']:
        cat_file = os.path.join(DATA_DIR, cat['file'])
        with open(cat_file, 'r', encoding='utf-8') as f:
            cat_data = json.load(f)

        category_name = cat['name']
        print(f"\n[{category_name}] {cat_data['count']} models")

        for product in cat_data['products']:
            model_id = product.get('model_id', '')
            if not model_id:
                continue

            safe_model = model_id.replace('/', '_').replace('\\', '_')
            save_dir = os.path.join(IMAGE_DIR, category_name, safe_model)
            save_path = os.path.join(save_dir, 'main_01.jpg')

            # Skip if already downloaded
            if os.path.exists(save_path):
                image_map[model_id] = f"image_codex/{category_name}/{safe_model}/main_01.jpg"
                continue

            url = get_model_image_url(model_id)
            success = download_image(url, save_path)

            if success:
                total_downloaded += 1
                image_map[model_id] = f"image_codex/{category_name}/{safe_model}/main_01.jpg"
                print(f"  OK: {model_id}")
            else:
                total_failed += 1
                if total_failed <= 5:
                    print(f"  FAIL: {model_id}")

            # Rate limiting
            time.sleep(0.3)

    # Save image map
    map_path = os.path.join(IMAGE_DIR, 'image_map.json')
    os.makedirs(IMAGE_DIR, exist_ok=True)
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(image_map, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Downloaded: {total_downloaded}, Failed: {total_failed}")
    print(f"Image map saved to: {map_path}")


if __name__ == '__main__':
    collect_images()

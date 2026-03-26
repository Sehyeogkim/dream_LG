#!/usr/bin/env python3
"""Collect product images from LG Korea website using Playwright.

Uses a headless browser to:
1. Navigate to LG product pages
2. Wait for dynamic content to load
3. Extract image URLs from og:image, gallery sections, or static CDN patterns
4. Download images to image_codex/{category}/{model_id}/

Focuses on categories that failed with the urllib approach.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Playwright is imported inside main() to allow top-level logic first
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
IMAGE_DIR = Path(__file__).resolve().parent.parent / 'image_codex'

# Map category names to LG URL slugs (multiple to try)
CATEGORY_SLUGS = {
    '공기청정기': ['air-purifier', 'air-care'],
    '공기청정가습기': ['air-purifier', 'air-care'],
    '제습기': ['dehumidifier', 'air-care'],
    'TV': ['tvs', 'oled-tv', 'nanocell-tv', 'tv'],
    '스타일러/슈케어': ['styler', 'shoe-care', 'clothing-care', 'tromm-styler'],
    '안마의자': ['massage-chair', 'healthcare'],
    '벽걸이에어컨': ['wall-air-conditioner', 'air-conditioner', 'residential-air-conditioner'],
    '세탁기/건조기': ['wash-combo', 'washing-machines', 'dryer', 'wash-tower', 'tromm-washer'],
    '냉장고': ['refrigerators', 'french-door-refrigerator', 'dios-refrigerator'],
    '상업용에어컨': ['system-air-conditioner', 'air-conditioner', 'commercial-air-conditioner'],
    '식기세척기': ['dishwashers', 'dishwasher'],
    '전기레인지': ['electric-range', 'cooking', 'induction-range'],
    '광파오븐': ['microwave-oven', 'oven', 'lightwave-oven'],
}

# Priority categories (ones that failed with urllib)
PRIORITY_CATEGORIES = [
    'TV', '스타일러/슈케어', '안마의자', '벽걸이에어컨',
    '상업용에어컨', '제습기', '식기세척기', '전기레인지', '광파오븐',
    '공기청정기', '공기청정가습기',
    '세탁기/건조기', '냉장고',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


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
    except Exception:
        return False


def extract_image_urls_from_page(page):
    """Extract product image URLs from a loaded page using multiple strategies."""
    urls = []

    # Strategy 1: og:image meta tag
    try:
        og = page.query_selector('meta[property="og:image"]')
        if og:
            content = og.get_attribute('content')
            if content and 'lge' in content:
                urls.append(('og:image', content))
    except Exception:
        pass

    # Strategy 2: Look for static.lge.co.kr gallery image URLs in page content
    try:
        html = page.content()

        # gallery medium/large images
        gallery_urls = re.findall(
            r'https?://static\.lge\.co\.kr/kr/images/[^"\'>\s]+/gallery/(?:medium|large)\d+\.jpg',
            html
        )
        for u in gallery_urls[:5]:
            urls.append(('gallery_regex', u))

        # Any static.lge.co.kr product image
        static_urls = re.findall(
            r'https?://static\.lge\.co\.kr/[^"\'>\s]+\.(?:jpg|png|webp)',
            html
        )
        # Filter for meaningful product images (not icons/logos)
        for u in static_urls:
            if any(kw in u.lower() for kw in ['gallery', 'product', 'medium', 'large', '/DZ/', '/D0/']):
                urls.append(('static_regex', u))

        # Extract md_number for constructing URLs
        md_matches = re.findall(r'(md\d{8,})', html)
        if md_matches:
            urls.append(('md_number', md_matches[0]))

    except Exception:
        pass

    # Strategy 3: Image elements in gallery/product sections
    try:
        selectors = [
            '.gallery img', '.product-image img', '.visual img',
            '.pdp-visual img', '.hero img', '.thumb img',
            'img.visual', 'img[src*="static.lge"]',
            '.css-1w8glao img',  # LG's React class patterns
        ]
        for sel in selectors:
            try:
                imgs = page.query_selector_all(sel)
                for img in imgs[:3]:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and ('lge' in src or 'lg.co.kr' in src):
                        urls.append((f'selector:{sel}', src))
            except Exception:
                pass
    except Exception:
        pass

    # Strategy 4: All img tags with lge.co.kr sources
    try:
        all_imgs = page.query_selector_all('img')
        for img in all_imgs:
            src = img.get_attribute('src') or img.get_attribute('data-src') or ''
            if 'static.lge.co.kr' in src and len(src) > 50:
                # Skip tiny icons
                if any(skip in src for skip in ['icon', 'logo', 'badge', 'btn', '1x1']):
                    continue
                urls.append(('img_tag', src))
    except Exception:
        pass

    return urls


def try_page_for_model(page, model_id, category_name, slugs):
    """Try various URL patterns to find the product page."""
    base_model = model_id.split('.')[0].lower()
    # Some models need the full ID
    full_model = model_id.replace('.', '-').lower()

    model_variants = [base_model, full_model]

    for slug in slugs:
        for model_var in model_variants:
            url = f"https://www.lge.co.kr/{slug}/{model_var}"
            try:
                response = page.goto(url, wait_until='domcontentloaded', timeout=15000)
                if response and response.status == 200:
                    # Wait for images to load
                    page.wait_for_timeout(2000)
                    # Check it's actually a product page (not 404 or redirect to listing)
                    title = page.title()
                    if 'Page not found' in title or '404' in title:
                        continue
                    # Check page has reasonable content
                    content_len = len(page.content())
                    if content_len < 5000:
                        continue
                    return url
            except Exception:
                continue

    # Strategy 2: Try LG search/product-detail direct URLs
    for slug in slugs:
        url = f"https://www.lge.co.kr/{slug}/{base_model}#"
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=15000)
            if response and response.status == 200:
                page.wait_for_timeout(2000)
                content_len = len(page.content())
                if content_len > 5000:
                    return url
        except Exception:
            continue

    return None


def collect_images_for_product(page, model_id, category_name, save_dir):
    """Collect images for a single product. Returns list of saved paths."""
    slugs = CATEGORY_SLUGS.get(category_name, [])
    saved = []

    page_url = try_page_for_model(page, model_id, category_name, slugs)
    if not page_url:
        return saved

    # Extract images
    image_urls = extract_image_urls_from_page(page)

    if not image_urls:
        return saved

    # Deduplicate and prioritize
    seen = set()
    ordered = []
    # Priority: og:image first, then gallery, then others
    for source, url in image_urls:
        if source == 'md_number':
            continue  # Handle separately
        normalized = url.split('?')[0]
        if normalized not in seen:
            seen.add(normalized)
            ordered.append((source, url))

    # Also construct URLs from md_number if found
    md_numbers = [u for s, u in image_urls if s == 'md_number']
    if md_numbers:
        md = md_numbers[0]
        # Try to figure out the slug that worked
        current_url = page.url
        for slug in slugs:
            if slug in current_url:
                for i in range(1, 4):
                    img_url = f"https://static.lge.co.kr/kr/images/{slug}/{md}/gallery/medium{i:02d}.jpg"
                    if img_url not in seen:
                        seen.add(img_url)
                        ordered.append(('md_constructed', img_url))
                break

    # Download main image
    if ordered:
        main_path = os.path.join(save_dir, 'main_01.jpg')
        for source, url in ordered:
            if download_image(url, main_path):
                saved.append(main_path)
                break

    # Download additional gallery images (sub_01, sub_02)
    sub_count = 0
    for source, url in ordered[1:]:
        if sub_count >= 2:
            break
        sub_count += 1
        sub_path = os.path.join(save_dir, f'sub_{sub_count:02d}.jpg')
        if download_image(url, sub_path):
            saved.append(sub_path)

    return saved


def has_existing_image(category_name, model_id):
    """Check if we already have an image for this model in any location."""
    safe_model = model_id.replace('/', '_').replace('\\', '_')

    # Direct category path
    main_path = IMAGE_DIR / category_name / safe_model / 'main_01.jpg'
    if main_path.exists():
        return True

    # Check in sheet_name-based subdirs (e.g., 세탁기/건조기 stored as 세탁기/건조기/)
    for subdir in IMAGE_DIR.iterdir():
        if not subdir.is_dir():
            continue
        # Check direct match
        p = subdir / safe_model / 'main_01.jpg'
        if p.exists():
            return True
        # Check one level deeper (세탁기/건조기)
        for subsub in subdir.iterdir():
            if subsub.is_dir():
                p = subsub / safe_model / 'main_01.jpg'
                if p.exists():
                    return True

    return False


def generate_test_html(image_map):
    """Generate an HTML page to verify downloaded images."""
    html_path = IMAGE_DIR / 'test_images.html'

    rows = []
    for cat, models in image_map.items():
        for model_id, paths in models.items():
            img_tags = ''.join(
                f'<img src="../{p}" style="max-height:150px;margin:4px;" '
                f'onerror="this.style.border=\'3px solid red\';this.alt=\'BROKEN\'" />'
                for p in paths
            )
            rows.append(
                f'<tr><td>{cat}</td><td>{model_id}</td>'
                f'<td>{img_tags}</td><td>{len(paths)}</td></tr>'
            )

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>LG Product Image Verification</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 20px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: middle; }}
th {{ background: #333; color: #fff; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
img {{ border: 1px solid #ccc; border-radius: 4px; }}
.summary {{ margin: 20px 0; padding: 15px; background: #e8f5e9; border-radius: 8px; }}
</style>
</head>
<body>
<h1>LG Product Image Verification</h1>
<div class="summary">
<strong>Total products with images:</strong> {sum(len(m) for m in image_map.values())}<br>
<strong>Total image files:</strong> {sum(len(p) for m in image_map.values() for p in m.values())}<br>
<strong>Categories:</strong> {len(image_map)}
</div>
<table>
<thead><tr><th>Category</th><th>Model ID</th><th>Images</th><th>Count</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
<script>
// Count broken images
window.onload = function() {{
    const broken = document.querySelectorAll('img[alt="BROKEN"]').length;
    const total = document.querySelectorAll('img').length;
    const el = document.createElement('div');
    el.className = 'summary';
    el.innerHTML = '<strong>Image Load Results:</strong> ' +
        (total - broken) + '/' + total + ' loaded OK, ' +
        broken + ' broken';
    el.style.background = broken > 0 ? '#ffebee' : '#e8f5e9';
    document.body.insertBefore(el, document.querySelector('table'));
}};
</script>
</body>
</html>"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\nTest HTML saved to: {html_path}")
    return html_path


def main():
    from playwright.sync_api import sync_playwright

    with open(DATA_DIR / 'meta.json', 'r', encoding='utf-8') as f:
        meta = json.load(f)

    # Build lookup: category_name -> list of products needing images
    to_collect = {}
    for cat in meta['categories']:
        cat_name = cat['name']
        cat_file = DATA_DIR / cat['file']
        with open(cat_file, 'r', encoding='utf-8') as f:
            cat_data = json.load(f)

        missing = []
        for product in cat_data['products']:
            model_id = product.get('model_id', '')
            if not model_id:
                continue
            if not has_existing_image(cat_name, model_id):
                missing.append(model_id)

        if missing:
            to_collect[cat_name] = missing

    total_missing = sum(len(v) for v in to_collect.values())
    print(f"Total products missing images: {total_missing}")
    for cat, models in to_collect.items():
        print(f"  {cat}: {len(models)} missing")
    print()

    if total_missing == 0:
        print("All products have images!")
        return

    # Sort categories by priority
    sorted_cats = sorted(
        to_collect.keys(),
        key=lambda c: PRIORITY_CATEGORIES.index(c) if c in PRIORITY_CATEGORIES else 99
    )

    image_map = {}  # cat -> {model_id: [relative_paths]}
    stats = {'downloaded': 0, 'failed': 0, 'skipped': 0}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ko-KR',
            viewport={'width': 1280, 'height': 900},
        )
        page = context.new_page()

        # Block unnecessary resources to speed up
        def route_handler(route):
            if route.request.resource_type in ['font', 'stylesheet', 'media']:
                route.abort()
            else:
                route.continue_()

        page.route('**/*', route_handler)

        for cat_name in sorted_cats:
            models = to_collect[cat_name]
            print(f"\n{'='*60}")
            print(f"[{cat_name}] Processing {len(models)} missing models...")
            print(f"{'='*60}")

            cat_image_map = {}

            for i, model_id in enumerate(models):
                safe_model = model_id.replace('/', '_').replace('\\', '_')
                save_dir = str(IMAGE_DIR / cat_name / safe_model)

                print(f"  [{i+1}/{len(models)}] {model_id}...", end=' ', flush=True)

                try:
                    saved = collect_images_for_product(page, model_id, cat_name, save_dir)
                    if saved:
                        rel_paths = [
                            str(Path(p).relative_to(IMAGE_DIR.parent))
                            for p in saved
                        ]
                        cat_image_map[model_id] = rel_paths
                        stats['downloaded'] += 1
                        print(f"OK ({len(saved)} images)")
                    else:
                        stats['failed'] += 1
                        print("FAIL")
                except Exception as e:
                    stats['failed'] += 1
                    print(f"ERROR: {e}")

                # Rate limiting
                time.sleep(0.5)

            if cat_image_map:
                image_map[cat_name] = cat_image_map

        browser.close()

    # Also add existing images to the map for the HTML report
    for cat in meta['categories']:
        cat_name = cat['name']
        cat_file = DATA_DIR / cat['file']
        with open(cat_file, 'r', encoding='utf-8') as f:
            cat_data = json.load(f)

        if cat_name not in image_map:
            image_map[cat_name] = {}

        for product in cat_data['products']:
            model_id = product.get('model_id', '')
            if not model_id or model_id in image_map[cat_name]:
                continue
            if has_existing_image(cat_name, model_id):
                safe_model = model_id.replace('/', '_').replace('\\', '_')
                # Find the actual path
                for subdir in IMAGE_DIR.iterdir():
                    if not subdir.is_dir():
                        continue
                    for root, dirs, files in os.walk(subdir):
                        if safe_model in root and 'main_01.jpg' in files:
                            rel = str(Path(root).relative_to(IMAGE_DIR.parent))
                            image_map[cat_name][model_id] = [f"{rel}/main_01.jpg"]
                            break

    # Generate test HTML
    generate_test_html(image_map)

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Failed:     {stats['failed']}")
    total_images = sum(
        1 for cat_dir in IMAGE_DIR.iterdir() if cat_dir.is_dir()
        for _ in cat_dir.rglob('main_01.jpg')
    )
    print(f"  Total images on disk: {total_images}")


if __name__ == '__main__':
    main()

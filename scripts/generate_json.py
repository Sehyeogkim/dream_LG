#!/usr/bin/env python3
"""Parse Excel file and generate JSON data files for the website."""
import json
import os
import sys
from datetime import datetime

import openpyxl

# Add parent to path so we can import parsers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.parsers import SHEET_PARSER_MAP, parse_sheet

EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'excel_files',
    '26년 3월 B2B 단체 가전구독 TABLE_0304.xlsx',
)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Loading Excel: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

    categories = []
    all_products = []
    total_count = 0

    for sheet_name in wb.sheetnames:
        if sheet_name not in SHEET_PARSER_MAP:
            print(f"  Skipping unknown sheet: {sheet_name}")
            continue

        ws = wb[sheet_name]
        products, category_name = parse_sheet(ws, sheet_name)
        count = len(products)
        total_count += count
        print(f"  {sheet_name} -> {category_name}: {count} products")

        if count == 0:
            continue

        # Save category JSON
        cat_filename = f"{sheet_name}.json"
        cat_data = {
            'category': category_name,
            'sheet_name': sheet_name,
            'count': count,
            'products': products,
        }
        cat_path = os.path.join(DATA_DIR, cat_filename)
        with open(cat_path, 'w', encoding='utf-8') as f:
            json.dump(cat_data, f, ensure_ascii=False, indent=2)

        categories.append({
            'name': category_name,
            'sheet_name': sheet_name,
            'file': cat_filename,
            'count': count,
        })

        for p in products:
            p['category'] = category_name
            all_products.append(p)

    # Save meta.json
    meta = {
        'updated': datetime.now().strftime('%Y-%m-%d'),
        'total_count': total_count,
        'categories': categories,
    }
    meta_path = os.path.join(DATA_DIR, 'meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Save master.json
    master_path = os.path.join(DATA_DIR, 'master.json')
    with open(master_path, 'w', encoding='utf-8') as f:
        json.dump({
            'updated': meta['updated'],
            'total_count': total_count,
            'categories': categories,
            'products': all_products,
        }, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {total_count} products across {len(categories)} categories")
    print(f"Output: {DATA_DIR}/")


if __name__ == '__main__':
    main()

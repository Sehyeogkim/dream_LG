"""Type D parser: TV.

Only 5yr and 6yr. 5 rows per product (qty tiers).
We extract ALL quantity tiers now.
Row structure per product group: 1대, 2~3대, 4~9대, 10~29대, 30대이상
"""
from openpyxl.utils import column_index_from_string as _col

DATA_START = 5
QTY_MAP = {
    '1대': '1', '기본': '1',
    '2~3대': '2-3', '2~3': '2-3',
    '4~9대': '4-9', '4~9': '4-9',
    '10~29대': '10-29', '10~29': '10-29', '10대~29대': '10-29',
    '30대': '30+', '30대 이상': '30+',
}


def _match_qty(f_str):
    for key, val in QTY_MAP.items():
        if key in f_str:
            return val
    return None


def parse_type_d(ws, sheet_name):
    # Collect raw data
    rows_data = []
    for row_idx in range(DATA_START, ws.max_row + 1):
        rows_data.append({
            'idx': row_idx,
            'B': ws.cell(row=row_idx, column=_col('B')).value,
            'C': ws.cell(row=row_idx, column=_col('C')).value,
            'D': ws.cell(row=row_idx, column=_col('D')).value,
            'E': ws.cell(row=row_idx, column=_col('E')).value,
            'F': ws.cell(row=row_idx, column=_col('F')).value,
            'G': ws.cell(row=row_idx, column=_col('G')).value,  # 5yr
            'J': ws.cell(row=row_idx, column=_col('J')).value,  # 6yr
        })

    # Group into products. Each product has 5 rows.
    products = []
    current_category = ''
    current_install = ''
    current_model = ''

    # Track product groups: accumulate qty tier prices
    current_prices = {'60': {}, '72': {}}

    for row in rows_data:
        if row['B']:
            # New product group starts
            if current_category and any(current_prices['60'].values()):
                products.append({
                    'model_id': current_model,
                    'product_name': current_category,
                    'install_type': current_install,
                    'prices': {k: dict(v) for k, v in current_prices.items() if v},
                })
            current_category = str(row['B']).strip().replace('\n', ' ')
            current_prices = {'60': {}, '72': {}}

        if row['C']:
            current_model = str(row['C']).strip().split('\n')[0]
        if row['D'] and not current_model:
            current_model = str(row['D']).strip().split('\n')[0]
        if row['E']:
            current_install = str(row['E']).strip().replace('\n', '/')

        if row['F'] is None:
            continue

        f_str = str(row['F']).strip()
        qty = _match_qty(f_str)
        if not qty:
            continue

        if row['G'] is not None and isinstance(row['G'], (int, float)):
            current_prices['60'][qty] = int(row['G'])
        if row['J'] is not None and isinstance(row['J'], (int, float)):
            current_prices['72'][qty] = int(row['J'])

    # Don't forget last product
    if current_category and any(current_prices['60'].values()):
        products.append({
            'model_id': current_model,
            'product_name': current_category,
            'install_type': current_install,
            'prices': {k: dict(v) for k, v in current_prices.items() if v},
        })

    return products

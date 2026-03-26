"""Type B parser: 세탁기/건조기.

Same layout as Type A but column E = 서비스타입 (not 평수).
"""
from openpyxl.utils import column_index_from_string


def _col(letter):
    return column_index_from_string(letter)


PRICE_COLS = {
    '36': _col('H'),
    '48': _col('Y'),
    '60': _col('AP'),
    '72': _col('BG'),
}

HEADER_ROW = 6
DATA_START = 7


def parse_type_b(ws, sheet_name):
    products = []
    current_category = ''
    current_name = ''
    current_model = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        b_val = ws.cell(row=row_idx, column=_col('B')).value
        c_val = ws.cell(row=row_idx, column=_col('C')).value
        d_val = ws.cell(row=row_idx, column=_col('D')).value
        e_val = ws.cell(row=row_idx, column=_col('E')).value  # 서비스타입
        f_val = ws.cell(row=row_idx, column=_col('F')).value  # 방문주기
        g_val = ws.cell(row=row_idx, column=_col('G')).value  # 기본 월요금

        if b_val:
            current_category = str(b_val).strip()
        if c_val:
            current_name = str(c_val).strip().replace('\n', ' ')
        if d_val:
            current_model = str(d_val).strip()

        if g_val is None:
            continue

        service_type = str(e_val).strip() if e_val else ''
        visit_cycle = f_val
        if visit_cycle is not None:
            visit_cycle = int(visit_cycle) if visit_cycle != 0 else 0

        prices = {}
        for period, col_idx in PRICE_COLS.items():
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None and isinstance(val, (int, float)):
                prices[period] = int(val)

        if not prices:
            continue

        visit_str = f"{visit_cycle}개월" if visit_cycle and visit_cycle > 0 else "방문없음"

        products.append({
            'model_id': current_model,
            'product_name': current_name,
            'category_sub': current_category,
            'service_type': service_type,
            'visit_cycle': visit_str,
            'prices': prices,
        })

    return _deduplicate(products)


def _deduplicate(products):
    """Group by model_id + service_type, keep cheapest visit option."""
    by_key = {}
    for p in products:
        key = (p['model_id'], p['service_type'])
        if key not in by_key:
            by_key[key] = p
        else:
            existing_36 = by_key[key]['prices'].get('36', float('inf'))
            new_36 = p['prices'].get('36', float('inf'))
            if new_36 < existing_36:
                by_key[key] = p
    return list(by_key.values())

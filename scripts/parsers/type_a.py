"""Type A parser: 공청기, 공청가습기, 제습기, 식기세척기, 전기레인지.

Structure:
  Row 6: headers (B=구분, C=구분, D=모델명, E=평수/용량, F=방문주기)
  Row 7+: data (merged cells for B, C, E across visit-cycle rows)
  Price columns (2~3대 할인가): H(3yr), Y(4yr), AP(5yr), BG(6yr)
"""
from openpyxl.utils import column_index_from_string


def _col(letter):
    return column_index_from_string(letter)


# Price columns for "2~3대" tier per contract year
PRICE_COLS = {
    '36': _col('H'),   # 3년
    '48': _col('Y'),   # 4년
    '60': _col('AP'),  # 5년
    '72': _col('BG'),  # 6년
}

HEADER_ROW = 6
DATA_START = 7


def parse_type_a(ws, sheet_name):
    products = []
    current_category = ''
    current_name = ''
    current_model = ''
    current_size = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        b_val = ws.cell(row=row_idx, column=_col('B')).value
        c_val = ws.cell(row=row_idx, column=_col('C')).value
        d_val = ws.cell(row=row_idx, column=_col('D')).value
        e_val = ws.cell(row=row_idx, column=_col('E')).value
        f_val = ws.cell(row=row_idx, column=_col('F')).value
        g_val = ws.cell(row=row_idx, column=_col('G')).value  # 기본 월요금

        if b_val:
            current_category = str(b_val).strip()
        if c_val:
            current_name = str(c_val).strip().replace('\n', ' ')
        if d_val:
            current_model = str(d_val).strip()
        if e_val:
            current_size = str(e_val).strip()

        # Skip rows without price data
        if g_val is None:
            continue

        visit_cycle = f_val
        if visit_cycle is not None:
            try:
                visit_cycle = int(visit_cycle) if visit_cycle != 0 else 0
            except (ValueError, TypeError):
                visit_cycle = 0  # Non-numeric visit cycle info

        prices = {}
        for period, col_idx in PRICE_COLS.items():
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None and isinstance(val, (int, float)):
                prices[period] = int(val)

        if not prices:
            continue

        product_name = current_name
        if current_size:
            product_name = f"{current_name} ({current_size})"

        visit_str = f"{visit_cycle}개월" if visit_cycle and visit_cycle > 0 else "방문없음"

        products.append({
            'model_id': current_model,
            'product_name': product_name,
            'category_sub': current_category,
            'size': current_size,
            'visit_cycle': visit_str,
            'prices': prices,
        })

    # Deduplicate: group by model_id, keep cheapest visit_cycle price for each period
    return _deduplicate(products)


def _deduplicate(products):
    """Group by model_id, pick the row with the lowest 3yr price (most affordable visit option)."""
    by_model = {}
    for p in products:
        mid = p['model_id']
        if mid not in by_model:
            by_model[mid] = p
        else:
            existing_36 = by_model[mid]['prices'].get('36', float('inf'))
            new_36 = p['prices'].get('36', float('inf'))
            if new_36 < existing_36:
                by_model[mid] = p
    return list(by_model.values())

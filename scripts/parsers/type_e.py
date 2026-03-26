"""Type E parser: 벽걸이에어컨.

Structure:
  Row 6: headers (B=구분, C=구분, D=모델명, E=서비스타입/방문주기)
  Row 7+: data
  Price cols (2~3대): K(3yr), AF(4yr), BA(5yr), BV(6yr)
"""
from openpyxl.utils import column_index_from_string


def _col(letter):
    return column_index_from_string(letter)


PRICE_COLS = {
    '36': _col('K'),
    '48': _col('AF'),
    '60': _col('BA'),
    '72': _col('BV'),
}

DATA_START = 7


def parse_type_e(ws, sheet_name):
    products = []
    current_category = ''
    current_name = ''
    current_model = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        b_val = ws.cell(row=row_idx, column=_col('B')).value
        c_val = ws.cell(row=row_idx, column=_col('C')).value
        d_val = ws.cell(row=row_idx, column=_col('D')).value
        e_val = ws.cell(row=row_idx, column=_col('E')).value  # 서비스타입
        f_val = ws.cell(row=row_idx, column=_col('F')).value  # 기본 월요금

        if b_val:
            current_category = str(b_val).strip()
        if c_val:
            current_name = str(c_val).strip().replace('\n', ' ')
        if d_val:
            current_model = str(d_val).strip()

        if f_val is None:
            continue

        service_type = str(e_val).strip() if e_val else ''

        prices = {}
        for period, col_idx in PRICE_COLS.items():
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None and isinstance(val, (int, float)):
                prices[period] = int(val)

        if not prices:
            continue

        products.append({
            'model_id': current_model,
            'product_name': f"{current_category} {current_name}".strip(),
            'service_type': service_type,
            'prices': prices,
        })

    return _deduplicate(products)


def _deduplicate(products):
    by_key = {}
    for p in products:
        key = (p['model_id'], p['service_type'])
        if key not in by_key:
            by_key[key] = p
    return list(by_key.values())

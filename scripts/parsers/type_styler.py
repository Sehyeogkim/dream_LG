"""Styler/ShuCare parser: 스타일러,슈케어.

Structure:
  Row 3-5: headers
  Row 6+: data
  Cols: D=제품, E=모델명, F=서비스타입, G=방문주기
  Price cols (2~3대): J(3yr), X(4yr), AL(5yr), AZ(6yr)
"""
from openpyxl.utils import column_index_from_string


def _col(letter):
    return column_index_from_string(letter)


PRICE_COLS = {
    '36': _col('J'),
    '48': _col('X'),
    '60': _col('AL'),
    '72': _col('AZ'),
}

DATA_START = 6


def parse_type_styler(ws, sheet_name):
    products = []
    current_product = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        d_val = ws.cell(row=row_idx, column=_col('D')).value
        e_val = ws.cell(row=row_idx, column=_col('E')).value  # 모델명
        f_val = ws.cell(row=row_idx, column=_col('F')).value  # 서비스타입
        g_val = ws.cell(row=row_idx, column=_col('G')).value  # 방문주기
        h_val = ws.cell(row=row_idx, column=_col('H')).value  # 기본 월요금

        if d_val:
            current_product = str(d_val).strip().replace('\n', ' ')

        if not e_val or h_val is None:
            continue

        model_id = str(e_val).strip()
        service_type = str(f_val).strip() if f_val else ''
        visit_cycle = str(g_val).strip() if g_val else ''

        prices = {}
        for period, col_idx in PRICE_COLS.items():
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None and isinstance(val, (int, float)):
                prices[period] = int(val)

        if not prices:
            continue

        products.append({
            'model_id': model_id,
            'product_name': current_product,
            'service_type': service_type,
            'visit_cycle': visit_cycle,
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

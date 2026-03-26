"""Massage chair parser: 안마의자.

Structure:
  Row 3-5: headers
  Row 6+: data
  Cols: C=제품군, D=모델명, E=방문주기
  Price cols (2~3대): H(3yr), V(4yr), AJ(5yr), AX(6yr)
"""
from openpyxl.utils import column_index_from_string


def _col(letter):
    return column_index_from_string(letter)


PRICE_COLS = {
    '36': _col('H'),
    '48': _col('V'),
    '60': _col('AJ'),
    '72': _col('AX'),
}

DATA_START = 6


def parse_type_massage(ws, sheet_name):
    products = []
    current_product_group = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        c_val = ws.cell(row=row_idx, column=_col('C')).value
        d_val = ws.cell(row=row_idx, column=_col('D')).value  # 모델명
        e_val = ws.cell(row=row_idx, column=_col('E')).value  # 방문주기
        f_val = ws.cell(row=row_idx, column=_col('F')).value  # 기본 월요금

        if c_val:
            current_product_group = str(c_val).strip().replace('\n', ' ')

        if not d_val or f_val is None:
            continue

        model_id = str(d_val).strip().split('\n')[0]  # Take first model if multiple
        visit_cycle = str(e_val).strip() if e_val else ''

        prices = {}
        for period, col_idx in PRICE_COLS.items():
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None and isinstance(val, (int, float)):
                prices[period] = int(val)

        if not prices:
            continue

        products.append({
            'model_id': model_id,
            'product_name': current_product_group,
            'visit_cycle': visit_cycle,
            'prices': prices,
        })

    return products

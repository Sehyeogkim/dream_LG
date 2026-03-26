"""Commercial AC parser: 상업용에어컨.

Only 3yr. B=제품군, C=모델명, D=방문주기, E=서비스타입
Price cols: F(1대), G(2-3), I(4-9), K(10-29), M(30+)
"""
from openpyxl.utils import column_index_from_string as _col

PRICE_COLS = {
    '36': {'1': _col('F'), '2-3': _col('G'), '4-9': _col('I'), '10-29': _col('K'), '30+': _col('M')},
}

DATA_START = 6


def parse_type_commercial_ac(ws, sheet_name):
    products = []
    current_product_group = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        b_val = ws.cell(row=row_idx, column=_col('B')).value
        c_val = ws.cell(row=row_idx, column=_col('C')).value
        d_val = ws.cell(row=row_idx, column=_col('D')).value
        e_val = ws.cell(row=row_idx, column=_col('E')).value
        f_val = ws.cell(row=row_idx, column=_col('F')).value

        if b_val:
            current_product_group = str(b_val).strip().replace('\n', ' ')

        if f_val is None:
            continue

        model_id = str(c_val).strip() if c_val else ''
        if not model_id:
            continue

        service_type = str(e_val).strip() if e_val else ''
        visit_cycle = str(d_val).strip() if d_val else ''

        prices = {}
        for period, tier_cols in PRICE_COLS.items():
            period_prices = {}
            for tier, col_idx in tier_cols.items():
                val = ws.cell(row=row_idx, column=col_idx).value
                if val is not None and isinstance(val, (int, float)):
                    period_prices[tier] = int(val)
            if period_prices:
                prices[period] = period_prices

        if not prices:
            continue

        products.append({
            'model_id': model_id,
            'product_name': current_product_group,
            'service_type': service_type,
            'visit_cycle': visit_cycle,
            'prices': prices,
        })

    return products

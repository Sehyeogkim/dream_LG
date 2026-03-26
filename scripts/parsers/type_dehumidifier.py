"""제습기 parser - unique layout.

Headers at row 5: B=구분, C=모델명, D=방문주기
Price cols (2~3대): F(3yr), W(4yr), AN(5yr), BE(6yr)
Data starts row 6.
"""
from openpyxl.utils import column_index_from_string


def _col(letter):
    return column_index_from_string(letter)


PRICE_COLS = {
    '36': _col('F'),
    '48': _col('W'),
    '60': _col('AN'),
    '72': _col('BE'),
}

DATA_START = 6


def parse_type_dehumidifier(ws, sheet_name):
    products = []
    current_name = ''
    current_model = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        b_val = ws.cell(row=row_idx, column=_col('B')).value
        c_val = ws.cell(row=row_idx, column=_col('C')).value
        d_val = ws.cell(row=row_idx, column=_col('D')).value  # 방문주기
        e_val = ws.cell(row=row_idx, column=_col('E')).value  # 기본 월요금

        if b_val:
            current_name = str(b_val).strip().replace('\n', ' ')
        if c_val:
            current_model = str(c_val).strip()

        if e_val is None:
            continue

        prices = {}
        for period, col_idx in PRICE_COLS.items():
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None and isinstance(val, (int, float)):
                prices[period] = int(val)

        if not prices:
            continue

        visit_cycle = ''
        if d_val is not None:
            try:
                vc = int(d_val)
                visit_cycle = f"{vc}개월" if vc > 0 else "방문없음"
            except (ValueError, TypeError):
                visit_cycle = str(d_val).strip()

        products.append({
            'model_id': current_model,
            'product_name': current_name,
            'visit_cycle': visit_cycle,
            'prices': prices,
        })

    # Deduplicate by model_id, keep cheapest
    by_model = {}
    for p in products:
        mid = p['model_id']
        if mid not in by_model:
            by_model[mid] = p
        else:
            existing = by_model[mid]['prices'].get('36', float('inf'))
            new = p['prices'].get('36', float('inf'))
            if new < existing:
                by_model[mid] = p
    return list(by_model.values())

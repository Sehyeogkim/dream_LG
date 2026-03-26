"""Type C parser: 냉장고, 광파오븐, 식기세척기, 전기레인지.

Structure:
  Row 8: sub-headers
  Row 9+: data (one row per model+service_type combo)
  Cols: D=구분1, E=구분2, F=모델명, G=서비스타입, H=방문주기

냉장고 price cols (2~3대): K(3yr), Y(4yr), AM(5yr), BA(6yr)
광파오븐 price cols (2~3대): L(3yr), AA(4yr), AP(5yr), BE(6yr)
"""
from openpyxl.utils import column_index_from_string


def _col(letter):
    return column_index_from_string(letter)


PRICE_COLS_MAP = {
    '냉장고': {
        '36': _col('K'),
        '48': _col('Y'),
        '60': _col('AM'),
        '72': _col('BA'),
    },
    '광파오븐': {
        '36': _col('L'),
        '48': _col('AA'),
        '60': _col('AP'),
        '72': _col('BE'),
    },
    '식기세척기': {
        '36': _col('L'),
        '48': _col('AA'),
        '60': _col('AP'),
        '72': _col('BE'),
    },
    '전기레인지': {
        '36': _col('L'),
        '48': _col('AA'),
        '60': _col('AP'),
        '72': _col('BE'),
    },
}

DATA_START = 9


def parse_type_c(ws, sheet_name):
    price_cols = PRICE_COLS_MAP.get(sheet_name, PRICE_COLS_MAP['냉장고'])
    products = []
    current_cat1 = ''
    current_cat2 = ''

    for row_idx in range(DATA_START, ws.max_row + 1):
        d_val = ws.cell(row=row_idx, column=_col('D')).value
        e_val = ws.cell(row=row_idx, column=_col('E')).value
        f_val = ws.cell(row=row_idx, column=_col('F')).value  # 모델명
        g_val = ws.cell(row=row_idx, column=_col('G')).value  # 서비스타입
        h_val = ws.cell(row=row_idx, column=_col('H')).value  # 방문주기

        if d_val:
            current_cat1 = str(d_val).strip().replace('\n', ' ')
        if e_val:
            current_cat2 = str(e_val).strip().replace('\n', ' ')

        if not f_val:
            continue

        model_id = str(f_val).strip()
        service_type = str(g_val).strip() if g_val else ''
        visit_cycle = ''
        if h_val is not None:
            try:
                vc = int(h_val)
                visit_cycle = f"{vc}개월" if vc > 0 else "방문없음"
            except (ValueError, TypeError):
                visit_cycle = str(h_val).strip()

        prices = {}
        for period, col_idx in price_cols.items():
            val = ws.cell(row=row_idx, column=col_idx).value
            if val is not None and isinstance(val, (int, float)):
                prices[period] = int(val)

        if not prices:
            continue

        product_name = f"{current_cat1} {current_cat2}".strip()

        products.append({
            'model_id': model_id,
            'product_name': product_name,
            'service_type': service_type,
            'visit_cycle': visit_cycle,
            'prices': prices,
        })

    return _deduplicate(products)


def _deduplicate(products):
    """Group by model_id, keep first occurrence (usually 라이트 or 프리미엄)."""
    by_model = {}
    for p in products:
        mid = p['model_id']
        if mid not in by_model:
            by_model[mid] = p
    return list(by_model.values())

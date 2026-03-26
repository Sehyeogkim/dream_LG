"""Sheet parser registry and dispatch."""
from openpyxl.utils import get_column_letter, column_index_from_string

from .type_a import parse_type_a
from .type_b import parse_type_b
from .type_c import parse_type_c
from .type_d import parse_type_d
from .type_e import parse_type_e
from .type_styler import parse_type_styler
from .type_massage import parse_type_massage
from .type_commercial_ac import parse_type_commercial_ac
from .type_dehumidifier import parse_type_dehumidifier

# sheet_name -> (parser_function, display_category_name)
SHEET_PARSER_MAP = {
    '공청기':        (parse_type_a, '공기청정기'),
    '공청가습기':    (parse_type_a, '공기청정가습기'),
    '제습기':        (parse_type_dehumidifier, '제습기'),
    '식기세척기':    (parse_type_c, '식기세척기'),
    '전기레인지':    (parse_type_c, '전기레인지'),
    '세탁기,건조기': (parse_type_b, '세탁기/건조기'),
    '냉장고':        (parse_type_c, '냉장고'),
    '광파오븐':      (parse_type_c, '광파오븐'),
    'TV':            (parse_type_d, 'TV'),
    '벽걸이에어컨':  (parse_type_e, '벽걸이에어컨'),
    '스타일러,슈케어': (parse_type_styler, '스타일러/슈케어'),
    '안마의자':      (parse_type_massage, '안마의자'),
    '상업용에어컨':  (parse_type_commercial_ac, '상업용에어컨'),
}


def parse_sheet(ws, sheet_name):
    """Parse a worksheet and return list of product dicts."""
    if sheet_name not in SHEET_PARSER_MAP:
        return [], sheet_name
    parser_fn, category_name = SHEET_PARSER_MAP[sheet_name]
    products = parser_fn(ws, sheet_name)
    return products, category_name

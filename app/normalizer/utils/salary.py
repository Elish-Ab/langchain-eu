import re
from typing import Optional

ALLOWED_HIGH_SALARY_CURRENCIES = {"USD", "EUR", "GBP"}

_CURRENCY_MAP = {
    "$": "USD", "USD": "USD", "usd": "USD",
    "€": "EUR", "EUR": "EUR", "eur": "EUR",
    "£": "GBP", "GBP": "GBP", "gbp": "GBP",
}

_NUM_RE = re.compile(r"\d{1,3}(?:,\d{3})+|\d{5,}")

def min_amount_from_llm_salary(salary: str) -> Optional[int]:
    if not salary:
        return None
    s = salary.strip()

    cur_before = re.search(r"(USD|EUR|GBP|\$|€|£)\s*(" + _NUM_RE.pattern + ")", s, flags=re.I)
    if cur_before:
        cur_raw, num_raw = cur_before.group(1), cur_before.group(2)
        cur = _CURRENCY_MAP.get(cur_raw)
        if cur in ALLOWED_HIGH_SALARY_CURRENCIES:
            return int(num_raw.replace(",", ""))

    num_after = re.search(r"(" + _NUM_RE.pattern + r")\s*(USD|EUR|GBP|\$|€|£)", s, flags=re.I)
    if num_after:
        num_raw, cur_raw = num_after.group(1), num_after.group(2)
        cur = _CURRENCY_MAP.get(cur_raw)
        if cur in ALLOWED_HIGH_SALARY_CURRENCIES:
            return int(num_raw.replace(",", ""))

    return None

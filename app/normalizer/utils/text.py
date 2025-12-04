from bs4 import BeautifulSoup
from typing import Optional, Iterable, List

def strip_html(html: Optional[str]) -> str:
    if not html:
        return ""
    return " ".join(BeautifulSoup(html, "html.parser").get_text().split()).strip()

def unique_keep_order(items: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for x in items or []:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

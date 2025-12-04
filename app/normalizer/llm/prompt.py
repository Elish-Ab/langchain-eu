from typing import Dict, Any
from app.normalizer.vocab.categories import JOB_CATEGORIES
from app.normalizer.vocab.types import JOB_TYPES
from app.normalizer.vocab.tags import JOB_TAGS_WHITELIST
from app.normalizer.vocab.benefits import BENEFITS_WHITELIST
from app.normalizer.vocab.regions import REGION_VALUES

SYSTEM = (
    "You extract structured job info and classify into CLOSED SETS. "
    "Return ONLY valid JSON for the provided schema.\n"
    "Guidelines:\n"
    "- company_name: exact employer/brand (plain text, no URL). If unknown, return empty string.\n"
    "- company_website: if explicitly present in text, return it as a URL, else empty string.\n"
    "- job_category: choose ONE from Job Categories or empty string if unclear (title has priority).\n"
    "- job_tags: choose ONLY items that EXACTLY match the Job Tags whitelist (verbatim strings).\n"
    "- benefits: choose ONLY items that EXACTLY match the Job Benefits whitelist (verbatim strings).\n"
    "- job_type: choose ONLY items from the Job Types whitelist; map synonyms from hints/description "
    "  (e.g., 'Full time'/'FT' → 'full-time'). Include multiple if explicitly present.\n"
    "- job_region: choose ONE OR MORE from Job Regions (if multiple regions are explicitly mentioned); otherwise empty string.map hints or text.\n"
    "- salary: return a normalized string based on the text: "
    "  • convert 'k' to full numbers with thousand separators (e.g., '90k' → '90,000'); "
    "  • keep the currency symbol/code; "
    "  • ranges as '£90,000–£120,000'; "
    "  • if the text is a lower bound (e.g., 'from £90k'), format as '£90,000+'; "
    "  • drop non-monetary add-ons like '+ bonus' or 'plus benefits'. If unknown, return empty string.\n"
    "Return JSON with keys: company_name, company_website, job_category, benefits[], job_tags[], job_type[], job_region, salary."
)

USER_TMPL = """INPUT (free text + hints):
{job_json}

CONTROLLED LISTS
- Job Categories: {job_categories}
- Job Types: {job_types}
- Job Tags: {job_tags}
- Job Benefits: {benefits}
- Job Regions: {regions}
"""

def build_prompt(job_json: str) -> Dict[str, Any]:
    return {
        "job_json": job_json,
        "job_categories": JOB_CATEGORIES,
        "job_types": JOB_TYPES,
        "job_tags": JOB_TAGS_WHITELIST,
        "benefits": BENEFITS_WHITELIST,
        "regions": REGION_VALUES,
    }

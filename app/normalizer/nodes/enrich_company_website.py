from app.normalizer.state import JobState
from app.integrations.companies_repo import fetch_company_website

def node_company_website_lookup(state: JobState) -> JobState:
    if not state.get("needs_company_website_lookup"):
        return state

    company_name = state["normalized"].get("company_name", "")
    website = fetch_company_website(company_name)

    if website:
        state["company_website"] = website

    return state

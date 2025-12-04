from app.integrations.supabase_client import supabase

def fetch_company_website(company_name: str) -> str:
    if not company_name:
        return ""

    # exact match
    res = (
        supabase.table("companies")
        .select("company_website")
        .eq("company_name", company_name)
        .limit(1)
        .execute()
    )
    if res.data and res.data[0].get("company_website"):
        return res.data[0]["company_website"]

    # partial / ilike match fallback
    res = (
        supabase.table("companies")
        .select("company_website, company_name")
        .ilike("company_name", f"%{company_name}%")
        .limit(1)
        .execute()
    )
    if res.data and res.data[0].get("company_website"):
        return res.data[0]["company_website"]

    return ""

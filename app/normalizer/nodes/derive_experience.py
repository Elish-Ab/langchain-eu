from app.normalizer.state import JobState
from app.normalizer.utils.experience import split_tags_and_experience

def node_derive_experience(state: JobState) -> JobState:
    normalized = state["normalized"]

    tags_str = normalized.get("job_tags", "")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    cleaned_tags, experience_level = split_tags_and_experience(tags)

    # rewrite job_tags WITHOUT experience tags
    normalized["job_tags"] = ", ".join(cleaned_tags) if cleaned_tags else ""

    return {
        **state,
        "normalized": normalized,
        "experience_level": experience_level
    }

import importlib.util
import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))


_LLM_EXTRACT_PATH = Path(__file__).with_name("llm_extract.py")
_LLM_EXTRACT_SPEC = importlib.util.spec_from_file_location("llm_extract", _LLM_EXTRACT_PATH)
llm_extract = importlib.util.module_from_spec(_LLM_EXTRACT_SPEC)
assert _LLM_EXTRACT_SPEC and _LLM_EXTRACT_SPEC.loader
_LLM_EXTRACT_SPEC.loader.exec_module(llm_extract)

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "llm" / "schema.py"
_SCHEMA_SPEC = importlib.util.spec_from_file_location("schema", _SCHEMA_PATH)
schema = importlib.util.module_from_spec(_SCHEMA_SPEC)
assert _SCHEMA_SPEC and _SCHEMA_SPEC.loader
_SCHEMA_SPEC.loader.exec_module(schema)
JobOutputSchema = schema.JobOutputSchema


class _DummyPrompt:
    def __or__(self, other):
        return other


class _DummyChatPromptTemplate:
    @staticmethod
    def from_messages(_):
        return _DummyPrompt()


def test_llm_extract_skips_fallback_when_primary_succeeds(monkeypatch):
    calls = {"primary": 0, "fallback": 0}

    def _model(model_name=None):
        if model_name == "gpt-4o-mini":
            def invoke(_):
                calls["fallback"] += 1
                return JobOutputSchema(
                    company_name="Dealfront",
                    company_website="",
                    job_category="Design",
                    benefits=[],
                    job_tags=[],
                    job_type=[],
                    job_region=[],
                    salary="",
                )

            return types.SimpleNamespace(invoke=invoke)

        def invoke(_):
            calls["primary"] += 1
            return JobOutputSchema(
                company_name="Dealfront",
                company_website="",
                job_category="",
                benefits=[],
                job_tags=[],
                job_type=[],
                job_region=[],
                salary="",
            )

        return types.SimpleNamespace(invoke=invoke)

    monkeypatch.setattr(llm_extract, "ChatPromptTemplate", _DummyChatPromptTemplate)
    monkeypatch.setattr(llm_extract, "_model", _model)

    result = llm_extract.node_llm_extract({"payload": {"title": "example"}})

    assert calls == {"primary": 1, "fallback": 0}
    assert result["llm_fallback"] is None
    assert result["llm_merged"].job_category == ""


def test_llm_extract_uses_fallback_when_primary_fails(monkeypatch):
    calls = {"primary": 0, "fallback": 0}

    def _model(model_name=None):
        if model_name == "gpt-4o-mini":
            def invoke(_):
                calls["fallback"] += 1
                return JobOutputSchema(
                    company_name="Dealfront",
                    company_website="",
                    job_category="Design",
                    benefits=[],
                    job_tags=[],
                    job_type=[],
                    job_region=[],
                    salary="",
                )

            return types.SimpleNamespace(invoke=invoke)

        def invoke(_):
            calls["primary"] += 1
            raise RuntimeError("primary boom")

        return types.SimpleNamespace(invoke=invoke)

    monkeypatch.setattr(llm_extract, "ChatPromptTemplate", _DummyChatPromptTemplate)
    monkeypatch.setattr(llm_extract, "_model", _model)

    result = llm_extract.node_llm_extract({"payload": {"title": "example"}})

    assert calls == {"primary": 1, "fallback": 1}
    assert result["llm_primary"] is None
    assert result["llm_fallback"].job_category == "Design"
    assert result["llm_merged"].job_category == "Design"

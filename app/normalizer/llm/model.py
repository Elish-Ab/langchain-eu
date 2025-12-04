import os
from typing import Optional
from langchain_openai import ChatOpenAI
from app.normalizer.llm.schema import JobOutputSchema

def _model(model_name: Optional[str] = None):
    model_id = model_name or os.getenv("PRIMARY_MODEL", "gpt-4o")
    return ChatOpenAI(model=model_id, temperature=0).with_structured_output(JobOutputSchema)

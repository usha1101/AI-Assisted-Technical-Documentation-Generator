from pydantic import BaseModel, Field
from typing import List, Optional
import uuid


class CodeRequest(BaseModel):
    source_code: str
    complexity: str = "concise"  # Options: "concise" or "detailed"
    save_history: bool = True
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class DocStringResponse(BaseModel):
    entity_name: str
    entity_type: str
    original_code: str
    generated_docstring: str


class DocumentationResult(BaseModel):
    results: List[DocStringResponse]


class HistoryItem(BaseModel):
    id: str
    timestamp: str
    summary: str
    code_snippet: str
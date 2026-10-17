from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid


class DocstringStyle(str, Enum):
    CONCISE = "concise"
    DETAILED = "detailed"
    GOOGLE = "google"
    SPHINX = "sphinx"
    NUMPY = "numpy"


class ParameterInfo(BaseModel):
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None


class CodeRequest(BaseModel):
    source_code: str
    complexity: str = "concise"  # Backward-compatible: "concise" or "detailed"
    style: DocstringStyle = DocstringStyle.CONCISE
    save_history: bool = True
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class DocStringResponse(BaseModel):
    entity_name: str
    entity_type: str
    original_code: str
    generated_docstring: str
    line_number: Optional[int] = None
    end_line_number: Optional[int] = None
    parameters: Optional[List[ParameterInfo]] = None
    return_type: Optional[str] = None
    raises: Optional[List[str]] = None
    docstring_style: Optional[str] = "concise"


class DocumentationResult(BaseModel):
    results: List[DocStringResponse]
    entities_count: Optional[int] = None


class DocumentedFileResponse(BaseModel):
    original_code: str
    documented_code: str
    entities_count: int
    results: List[DocStringResponse]


class ParseErrorDetail(BaseModel):
    line: Optional[int] = None
    column: Optional[int] = None
    message: str
    text: Optional[str] = None


class HistoryItem(BaseModel):
    id: str
    timestamp: str
    summary: str
    code_snippet: str
    session_id: Optional[str] = None
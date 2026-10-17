import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import json
import os
from typing import List, Optional
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, PlainTextResponse

from app.models import (
    CodeRequest,
    DocStringResponse,
    DocumentationResult,
    DocumentedFileResponse,
    DocstringStyle,
    HistoryItem,
    ParameterInfo
)
from app.parser import CodeParser
from app.generator import get_generator, BaseGenerator
from app.formatter import DocstringFormatter
from app.injector import DocstringInjector
import uvicorn

# Global generator instance
generator: Optional[BaseGenerator] = None
parser = CodeParser()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown initialization."""
    global generator
    generator = get_generator()
    yield


app = FastAPI(
    title='AI-Assisted Tech Doc Generator',
    description='Automated technical documentation and docstring generation system using CodeT5 and AST analysis.',
    version='2.0.0',
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. SIMPLE PERSISTENCE ---
DB_FILE = "chat_history.json"


def load_db() -> list:
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_db(data: list):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


# --- 2. ENDPOINTS ---

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint reporting generator status and compute device."""
    return {
        "status": "healthy",
        "generator_type": type(generator).__name__ if generator else "uninitialized",
        "device": getattr(generator, 'device', 'cpu'),
        "timestamp": datetime.now().isoformat()
    }


@app.post('/generate-docs', response_model=DocumentationResult, tags=["Documentation"])
async def generate_docs(request: CodeRequest):
    """
    Parses Python source code and generates technical documentation for all
    detected classes, functions, and methods.
    """
    if not request.source_code or not request.source_code.strip():
        raise HTTPException(status_code=400, detail='Source code cannot be empty.')

    try:
        parsed_entities = parser.parse_code(request.source_code)
        results: List[DocStringResponse] = []

        for entity in parsed_entities:
            # Run inference in a threadpool to avoid blocking FastAPI's async event loop
            raw_summary = await asyncio.to_thread(
                generator.generate_docstring,
                entity['code'],
                request.complexity
            )

            # Format into requested docstring style (Google, Sphinx, NumPy, or Concise)
            formatted_docstring = DocstringFormatter.format_docstring(
                summary=raw_summary,
                parameters=entity.get('parameters'),
                return_type=entity.get('return_type'),
                raises=entity.get('raises'),
                style=request.style
            )

            param_objs = [
                ParameterInfo(
                    name=p['name'],
                    type_annotation=p.get('type_annotation'),
                    default_value=p.get('default_value')
                )
                for p in entity.get('parameters', [])
            ]

            results.append(DocStringResponse(
                entity_name=entity['name'],
                entity_type=entity['type'],
                original_code=entity['code'],
                generated_docstring=formatted_docstring,
                line_number=entity.get('line_number'),
                end_line_number=entity.get('end_line_number'),
                parameters=param_objs,
                return_type=entity.get('return_type'),
                raises=entity.get('raises'),
                docstring_style=request.style.value
            ))

        # Save to session history
        if request.save_history:
            history = load_db()
            title = results[0].entity_name if results else "Untitled Snippet"
            new_entry = {
                "id": str(uuid.uuid4()),
                "session_id": request.session_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "title": title,
                "results": [r.model_dump() for r in results]
            }
            history.insert(0, new_entry)
            save_db(history)

        return DocumentationResult(results=results, entities_count=len(results))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/generate-documented-file', response_model=DocumentedFileResponse, tags=["Documentation"])
async def generate_documented_file(request: CodeRequest):
    """
    Generates documentation and returns the entire Python file with newly
    generated docstrings injected directly beneath function and class declarations.
    """
    doc_result = await generate_docs(request)
    documented_entities = [r.model_dump() for r in doc_result.results]

    documented_code = DocstringInjector.inject_docstrings(
        source_code=request.source_code,
        entities=documented_entities
    )

    return DocumentedFileResponse(
        original_code=request.source_code,
        documented_code=documented_code,
        entities_count=len(doc_result.results),
        results=doc_result.results
    )


@app.post('/export-markdown', response_class=PlainTextResponse, tags=["Documentation"])
async def export_markdown(request: CodeRequest):
    """
    Exports generated technical documentation as ready-to-save GitHub-flavored Markdown.
    """
    doc_result = await generate_docs(request)

    md_lines = [
        f"# Technical Documentation",
        f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "---",
        ""
    ]

    for item in doc_result.results:
        md_lines.append(f"## `{item.entity_name}` ({item.entity_type.capitalize()})\n")
        md_lines.append(f"**Docstring:**\n")
        md_lines.append(f"```text\n{item.generated_docstring}\n```\n")
        md_lines.append(f"**Source Code:**\n")
        md_lines.append(f"```python\n{item.original_code}\n```\n")
        md_lines.append("---\n")

    return "\n".join(md_lines)


@app.get("/history/{session_id}", tags=["History"])
async def get_history(session_id: str):
    """Retrieve history for a specific user session."""
    all_history = load_db()
    user_history = [h for h in all_history if h.get("session_id") == session_id]
    return user_history


if __name__ == '__main__':
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)
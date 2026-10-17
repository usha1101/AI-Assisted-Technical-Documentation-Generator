import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.models import CodeRequest, HistoryItem
from app.parser import CodeParser
from app.generator import DocGenerator
import uvicorn

app = FastAPI(title='AI-Assisted Tech Doc Generator')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DATABASE (JSON FILE) ---
DB_FILE = "chat_history.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump([], f)


def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# --- 2. CORE LOGIC ---
parser = CodeParser()
generator = None


@app.on_event('startup')
async def startup_event():
    global generator
    generator = DocGenerator()


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post('/generate-docs')
async def generate_docs(request: CodeRequest):
    if not request.source_code:
        raise HTTPException(status_code=400, detail='Source code cannot be empty.')
    try:
        # Generate Docs
        parsed_entities = parser.parse_code(request.source_code)
        results = []
        for entity in parsed_entities:
            doc_text = generator.generate_docstring(entity['code'], request.complexity)
            results.append({
                "entity_name": entity['name'],
                "entity_type": entity['type'],
                "original_code": entity['code'],
                "generated_docstring": doc_text
            })

        # --- SAVE TO HISTORY (If not temporary) ---
        if request.save_history:
            history = load_db()
            # Create a short title from the first function name or first 20 chars
            title = results[0]['entity_name'] if results else "Untitled Snippet"

            new_entry = {
                "id": str(uuid.uuid4()),
                "session_id": request.session_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "title": title,
                "results": results
            }
            history.insert(0, new_entry)  # Add to top
            save_db(history)

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Retrieve history for a specific user session"""
    all_history = load_db()
    # Filter by session_id (simulating user account isolation)
    user_history = [h for h in all_history if h.get("session_id") == session_id]
    return user_history


if __name__ == '__main__':
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)
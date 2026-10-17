# AI-Assisted Technical Documentation Generator

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![HuggingFace](https://img.shields.io/badge/Model-Salesforce%2Fcodet5--base--multi--sum-yellow.svg)](https://huggingface.co/Salesforce/codet5-base-multi-sum)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent Python documentation system that decomposes source code using Python's native Abstract Syntax Tree (**AST**) and generates accurate, natural language docstrings and technical explanations using the **Salesforce CodeT5** transformer model.

---

## 1. Project Overview

Drafting comprehensive docstrings and technical documentation for large codebases is repetitive and time-consuming. This tool automates the process:

1. **Structural Analysis**: Inspects Python code using the `ast` module to isolate top-level functions, classes, and class methods.
2. **Local AI Summarization**: Feeds code snippets into `Salesforce/codet5-base-multi-sum`, a specialized sequence-to-sequence code summarization model running locally via Hugging Face `transformers` and PyTorch.
3. **Multi-Interface Access**: Provides both a high-performance **FastAPI** REST backend and an interactive **Streamlit** dark-themed chat UI.

---

## 2. Key Features

- **Interactive Streamlit UI**: Modern, dark-mode interface with floating prompt bar, Python (`.py`) file attachment, and session history tracking.
- **Precision AST Parsing**:
  - Automatically identifies functions, classes, and methods.
  - Ignores private/internal helper functions to prevent documentation clutter.
  - Accurately captures decorators (e.g., `@staticmethod`, `@functools.wraps`).
- **Local AI Inference**:
  - Powered by `Salesforce/codet5-base-multi-sum` (~890 MB).
  - Runs offline without requiring external paid API keys (OpenAI, Gemini, etc.).
  - Supports both **concise** and **detailed** complexity modes.
- **Robust REST API**:
  - FastAPI-powered backend with automatic Swagger documentation (`/docs`).
  - Session-isolated generation history.
- **Automated Stress Testing**:
  - Includes test scripts to validate against complex OOP patterns, decorators, and exception handling, logging timestamped reports to `results/`.

---

## 3. Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI | High-performance asynchronous REST API framework |
| **Server** | Uvicorn | ASGI web server |
| **Frontend UI** | Streamlit | Chat-based web user interface |
| **Parsing Engine** | Python `ast` | Abstract Syntax Tree parsing & source segmentation |
| **AI / ML** | Transformers & PyTorch | Hugging Face implementation of `Salesforce/codet5-base-multi-sum` |
| **Validation** | Pydantic | Typed schemas and request validation |
| **Storage** | JSON Flat File | Lightweight session history store |

---

## 4. Directory Structure

```text
AI-Assisted-Technical-Documentation-Generator/
├── app/
│   ├── __init__.py
│   ├── generator.py       # CodeT5 model integration (DocGenerator)
│   ├── main.py            # FastAPI application routes & server entry point
│   ├── models.py          # Pydantic request and response schemas
│   └── parser.py          # AST extraction logic (CodeParser)
├── frontend/
│   └── ui.py              # Streamlit interactive chat interface
├── results/               # Directory for automated test log outputs
│   └── .gitkeep
├── .gitignore             # Git ignore definitions
├── LICENSE                # MIT License
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
├── run_complex_test.py    # Integration test for complex code structures
└── test_api.py            # Quick API verification test script
```

---

## 5. Installation & Setup

### Prerequisites
- Python 3.9, 3.10, or 3.11 installed.
- (Optional) NVIDIA GPU with CUDA support for accelerated inference.

### 1. Clone the Repository
```bash
git clone https://github.com/usha1101/AI-Assisted-Technical-Documentation-Generator.git
cd AI-Assisted-Technical-Documentation-Generator
```

### 2. Create and Activate a Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 6. Running the Application

### Option A: Start the FastAPI Backend
Launch the backend server:
```bash
python -m app.main
```
- The backend starts at: `http://127.0.0.1:8000`
- Interactive API documentation (Swagger UI): `http://127.0.0.1:8000/docs`
- *Note: On the first launch, the AI model weights (~890 MB) will be downloaded automatically.*

### Option B: Start the Streamlit Frontend
In a new terminal (with the virtual environment activated):
```bash
streamlit run frontend/ui.py
```
- Open your browser at: `http://localhost:8501`
- **Default Sign-in Credentials**:
  - **Username**: `user`
  - **Password**: `1234`

---

## 7. Running Automated Tests

Ensure the FastAPI backend is running (`python -m app.main`), then execute:

- **Quick API Test:**
  ```bash
  python test_api.py
  ```

- **Complex Stress Test:**
  ```bash
  python run_complex_test.py
  ```
  *(Results will print in the console and save a timestamped summary log in the `results/` folder).*

---

## 8. License & Attribution

This project is open-source and distributed under the **[MIT License](LICENSE)**.

### Acknowledgments & Attribution
- **Original Author**: [Nithin Reddy](https://github.com/nithinreddy18) ([@nithinreddy18](https://github.com/nithinreddy18))
- **Maintainer**: [Usha](https://github.com/usha1101) ([@usha1101](https://github.com/usha1101))
- **Model**: [Salesforce CodeT5](https://github.com/salesforce/CodeT5) / [Salesforce/codet5-base-multi-sum](https://huggingface.co/Salesforce/codet5-base-multi-sum) on Hugging Face

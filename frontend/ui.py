import streamlit as st
import requests
import uuid
import time

# --- CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="AI Technical Doc Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8000"

# --- GEMINI-INSPIRED DARK CSS ---
st.markdown("""
<style>
    /* 1. Main Background Colors */
    .stApp {
        background-color: #131314;
        color: #E3E3E3;
    }

    /* 2. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E1F20;
        border-right: 1px solid #333;
    }

    /* 3. Floating Centered Input Bar */
    .stChatInputContainer {
        padding-bottom: 20px;
        background: transparent !important;
    }

    .stChatInputContainer > div {
        width: 65% !important;
        margin: auto;
        background-color: #282A2C !important;
        border-radius: 30px !important;
        border: 1px solid #444;
        padding: 5px 12px; 
    }

    .stChatInputContainer textarea:focus {
        box-shadow: none !important;
        border-color: #555 !important;
    }

    /* 4. Chat Bubbles */
    .stChatMessage {
        background-color: transparent !important;
    }

    /* 5. Tool Container */
    [data-testid="stFileUploader"] {
        padding: 10px;
        border: 1px dashed #555;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_user" not in st.session_state:
    st.session_state.current_user = "Guest"
if "file_content" not in st.session_state:
    st.session_state.file_content = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "last_documented_code" not in st.session_state:
    st.session_state.last_documented_code = None
if "last_markdown" not in st.session_state:
    st.session_state.last_markdown = None


# --- ACTIONS ---
def start_new_chat():
    st.session_state.messages = []
    st.session_state.file_content = None
    st.session_state.file_name = None
    st.session_state.last_documented_code = None
    st.session_state.last_markdown = None
    st.rerun()


def login():
    if st.session_state.login_user == "user" and st.session_state.login_pwd == "1234":
        st.session_state.authenticated = True
        st.session_state.current_user = "user"
        st.rerun()
    else:
        st.error("Invalid credentials. Try: user / 1234")


def logout():
    st.session_state.authenticated = False
    st.rerun()


# ==========================================
# 1. SIGN IN SCREEN
# ==========================================
if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("✨ Sign In")
        st.caption("AI-Assisted Technical Documentation Generator")
        st.text_input("Username", key="login_user")
        st.text_input("Password", type="password", key="login_pwd")
        st.button("Continue", on_click=login, type="primary", use_container_width=True)
    st.stop()


# ==========================================
# 2. MAIN APPLICATION
# ==========================================

# --- SIDEBAR ---
with st.sidebar:
    if st.button("➕ New Chat", type="primary", use_container_width=True):
        start_new_chat()

    st.markdown("---")

    # Options & Style Selector
    st.caption("CONFIGURATION")
    selected_style = st.selectbox(
        "Docstring Style",
        options=["google", "sphinx", "numpy", "concise", "detailed"],
        index=0,
        help="Choose the docstring format to generate."
    )

    st.markdown("---")

    # File Attachment
    st.caption("FILE ATTACHMENT")
    uploaded_file = st.file_uploader("Attach a file (.py)", type=["py"], label_visibility="collapsed")
    if uploaded_file:
        st.session_state.file_content = uploaded_file.getvalue().decode("utf-8")
        st.session_state.file_name = uploaded_file.name
        st.success(f"📎 Attached: {uploaded_file.name}")

    if st.session_state.file_content:
        if st.button("❌ Remove attached file", use_container_width=True):
            st.session_state.file_content = None
            st.session_state.file_name = None
            st.rerun()

    st.markdown("---")

    # History
    st.caption("RECENT SESSIONS")
    try:
        hist_resp = requests.get(f"{API_URL}/history/{st.session_state.session_id}", timeout=3)
        if hist_resp.status_code == 200:
            history_data = hist_resp.json()
            if history_data:
                for item in history_data:
                    title = item.get('title', 'Snippet')
                    display_title = (title[:18] + '..') if len(title) > 18 else title
                    if st.button(f"💬 {display_title}", key=item['id'], use_container_width=True):
                        # Load previous documentation directly into the chat view
                        st.session_state.messages = []
                        results = item.get("results", [])
                        hist_text = f"**Loaded Session:** `{title}` ({item.get('timestamp')})\n\n---\n"
                        for res in results:
                            hist_text += f"### `{res['entity_name']}` ({res['entity_type']})\n"
                            hist_text += f"{res['generated_docstring']}\n\n"
                            hist_text += f"```python\n{res['original_code']}\n```\n\n---\n"
                        st.session_state.messages.append({"role": "assistant", "content": hist_text})
                        st.rerun()
            else:
                st.caption("No past sessions yet.")
    except Exception:
        st.caption("Backend offline")

    st.markdown("---")
    c_p1, c_p2 = st.columns([3, 1])
    c_p1.markdown(f"**{st.session_state.current_user}**")
    c_p2.button("🚪", on_click=logout, help="Sign out")


# --- MAIN CHAT AREA ---

# Welcome Screen (Empty State)
if not st.session_state.messages:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.title(f"Hello, {st.session_state.current_user}")
    st.markdown("### Paste Python code below or attach a `.py` file to generate documentation.")

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "✨"):
        if "```" in msg["content"]:
            st.markdown(msg["content"])
        else:
            st.write(msg["content"])

# Export Downloads Toolbar (if documented code is available)
if st.session_state.last_documented_code or st.session_state.last_markdown:
    st.markdown("### 📥 Export Options")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.session_state.last_documented_code:
            st.download_button(
                label="📄 Download Documented Python Code (.py)",
                data=st.session_state.last_documented_code,
                file_name=f"documented_{st.session_state.file_name or 'code.py'}",
                mime="text/x-python",
                use_container_width=True
            )
    with col_d2:
        if st.session_state.last_markdown:
            st.download_button(
                label="📝 Download Documentation (.md)",
                data=st.session_state.last_markdown,
                file_name="documentation.md",
                mime="text/markdown",
                use_container_width=True
            )
    st.markdown("---")

# --- PROMPT INPUT BAR ---
if prompt := st.chat_input("Paste Python code or type a query..."):

    # Show User Input
    display_prompt = f"```python\n{prompt}\n```" if ("def " in prompt or "class " in prompt) else prompt
    st.session_state.messages.append({"role": "user", "content": display_prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(display_prompt)

    # Determine code to process
    final_code = st.session_state.file_content if st.session_state.file_content else prompt

    # Generate Documentation
    with st.chat_message("assistant", avatar="✨"):
        with st.status("Analyzing code & generating documentation...", expanded=True) as status:
            time.sleep(0.2)

            try:
                payload = {
                    "source_code": final_code,
                    "complexity": "detailed" if selected_style == "detailed" else "concise",
                    "style": selected_style,
                    "save_history": True,
                    "session_id": st.session_state.session_id
                }

                # 1. Generate Documented File
                file_resp = requests.post(f"{API_URL}/generate-documented-file", json=payload, timeout=60)

                # 2. Export Markdown
                md_resp = requests.post(f"{API_URL}/export-markdown", json=payload, timeout=60)

                if file_resp.status_code == 200:
                    data = file_resp.json()
                    results = data.get("results", [])
                    st.session_state.last_documented_code = data.get("documented_code", "")
                    if md_resp.status_code == 200:
                        st.session_state.last_markdown = md_resp.text

                    answer_text = f"### ✨ Generated Documentation ({len(results)} entities found)\n\n"
                    for item in results:
                        answer_text += f"#### `{item['entity_name']}` ({item['entity_type']})\n"
                        answer_text += f"```text\n{item['generated_docstring']}\n```\n"
                        answer_text += f"```python\n{item['original_code']}\n```\n\n---\n"

                    status.update(label="Complete", state="complete", expanded=False)
                    st.markdown(answer_text)
                    st.session_state.messages.append({"role": "assistant", "content": answer_text})
                    st.rerun()

                else:
                    status.update(label="Error", state="error")
                    st.error(f"Backend Error ({file_resp.status_code}): {file_resp.text}")

            except Exception as e:
                status.update(label="Connection Failed", state="error")
                st.error(f"Could not reach backend: {e}")
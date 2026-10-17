import streamlit as st
import requests
import uuid
import time

# --- CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Gemini-Style DocGen",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8000"

# --- GEMINI-INSPIRED CSS ---
# This styles the input bar to look exactly like the screenshot:
# Dark, rounded, floating in the middle-bottom.
st.markdown("""
<style>
    /* 1. Main Background Colors */
    .stApp {
        background-color: #131314; /* Gemini Dark Background */
        color: #E3E3E3;
    }

    /* 2. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E1F20;
        border-right: 1px solid #333;
    }

    /* 3. THE FLOATING INPUT BAR (Matches Screenshot) */
    .stChatInputContainer {
        padding-bottom: 20px;
        background: transparent !important;
    }

    .stChatInputContainer > div {
        width: 60% !important;  /* Center it like the screenshot */
        margin: auto;
        background-color: #282A2C !important; /* Pill Background */
        border-radius: 30px !important; /* Fully Rounded */
        border: 1px solid #444;
        padding: 5px 10px; 
    }

    /* Remove default focus border to keep it clean */
    .stChatInputContainer textarea:focus {
        box-shadow: none !important;
        border-color: #444 !important;
    }

    /* 4. Chat Bubbles */
    .stChatMessage {
        background-color: transparent !important;
    }

    /* 5. File Uploader Styling to look like a tool */
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


# --- ACTIONS ---
def start_new_chat():
    st.session_state.messages = []
    st.session_state.file_content = None
    st.rerun()


def login():
    if st.session_state.login_user == "user" and st.session_state.login_pwd == "1234":
        st.session_state.authenticated = True
        st.session_state.current_user = "user"
        st.rerun()
    else:
        st.error("Try: user / 1234")


def logout():
    st.session_state.authenticated = False
    st.rerun()


# ==========================================
# 1. LOGIN
# ==========================================
if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.title("✨ Sign In")
        st.text_input("Username", key="login_user")
        st.text_input("Password", type="password", key="login_pwd")
        st.button("Continue", on_click=login, type="primary", use_container_width=True)
    st.stop()

# ==========================================
# 2. MAIN INTERFACE
# ==========================================

# --- SIDEBAR (Tools & History) ---
with st.sidebar:
    # 1. NEW CHAT BUTTON (Prominent)
    if st.button("➕ New Chat", type="primary", use_container_width=True):
        start_new_chat()

    st.markdown("---")

    # 2. FILE UPLOAD (Mimicking the '+' attachment feel)
    st.caption("TOOLS")
    uploaded_file = st.file_uploader("Attach a file (.py)", type=["py"], label_visibility="collapsed")
    if uploaded_file:
        st.session_state.file_content = uploaded_file.getvalue().decode("utf-8")
        st.success(f"📎 Attached: {uploaded_file.name}")

    st.markdown("---")

    # 3. HISTORY
    st.caption("RECENT")
    try:
        hist = requests.get(f"{API_URL}/history/{st.session_state.session_id}")
        if hist.status_code == 200:
            for item in hist.json():
                # Truncate title for cleaner sidebar
                title = (item['title'][:18] + '..') if len(item['title']) > 18 else item['title']
                if st.button(f"💬 {title}", key=item['id']):
                    st.toast("History loaded (Mock)")
    except:
        st.warning("Offline Mode")

    # 4. BOTTOM PROFILE
    st.markdown("---")
    c_p1, c_p2 = st.columns([3, 1])
    c_p1.markdown(f"**{st.session_state.current_user}**")
    c_p2.button("🚪", on_click=logout)

# --- MAIN CHAT AREA ---

# Welcome Screen (Only if empty)
if not st.session_state.messages:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.title(f"Hello, {st.session_state.current_user}")
    st.markdown("### How can I help verify your code today?")

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "✨"):
        if "```" in msg["content"]:
            st.markdown(msg["content"])
        else:
            st.write(msg["content"])

# --- THE INPUT FIELD (Bottom, Floating, Centered) ---
# Note: The CSS above styles this to be a pill shape
if prompt := st.chat_input("Ask Gemini 3..."):

    # 1. Show User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(prompt)

    # 2. Determine Code Context
    # If a file is attached, we send that. If not, we check if the user pasted code.
    final_code = st.session_state.file_content if st.session_state.file_content else prompt

    # 3. Generate Answer
    with st.chat_message("assistant", avatar="✨"):
        # Status Indicator (The "Thinking" state)
        with st.status("Analyzing...", expanded=True) as status:
            time.sleep(0.5)  # UX Delay

            try:
                payload = {
                    "source_code": final_code,
                    "complexity": "detailed",
                    "save_history": True,
                    "session_id": st.session_state.session_id
                }

                response = requests.post(f"{API_URL}/generate-docs", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    answer_text = ""
                    for item in results:
                        answer_text += f"### {item['entity_name']} ({item['entity_type']})\n"
                        answer_text += f"{item['generated_docstring']}\n\n"
                        answer_text += f"```python\n{item['original_code']}\n```\n\n---\n"

                    status.update(label="Complete", state="complete", expanded=False)
                    st.markdown(answer_text)
                    st.session_state.messages.append({"role": "assistant", "content": answer_text})

                else:
                    status.update(label="Error", state="error")
                    st.error(f"Backend Error: {response.text}")

            except Exception as e:
                status.update(label="Connection Failed", state="error")
                st.error(f"Error: {e}")
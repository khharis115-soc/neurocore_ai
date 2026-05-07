import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
import sqlite3, time, hashlib, PyPDF2, docx

# Database Logic
def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

manage_db('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# --- FILE MEMORY (Gemini Style) ---
if "persistent_file_text" not in st.session_state:
    st.session_state.persistent_file_text = None
if "last_uploaded_filename" not in st.session_state:
    st.session_state.last_uploaded_filename = None
if "current_session" not in st.session_state:
    st.session_state.current_session = f"Chat_{int(time.time())}"

# Load Engine
API_KEY = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=API_KEY)

# --- SIDEBAR (Upload Section) ---
with st.sidebar:
    st.title("📁 File Lab")
    up_file = st.file_uploader("Upload File (PDF/Doc/Image)", type=['pdf','docx','txt','png','jpg'])
    
    # Jab bhi file upload ho, uska text nikaal kar memory mein save kar lo
    if up_file and up_file.name != st.session_state.last_uploaded_filename:
        st.session_state.last_uploaded_filename = up_file.name
        with st.spinner("Reading file..."):
            if up_file.type.startswith("image/"):
                st.session_state.persistent_file_text = Image.open(up_file)
            else:
                text = ""
                if up_file.name.endswith('.pdf'):
                    pdf = PyPDF2.PdfReader(up_file); text = " ".join([p.extract_text() for p in pdf.pages])
                elif up_file.name.endswith('.docx'):
                    doc = docx.Document(up_file); text = " ".join([p.text for p in doc.paragraphs])
                else:
                    text = up_file.read().decode()
                st.session_state.persistent_file_text = text
        st.success(f"Loaded: {up_file.name}")

# --- CHAT INTERFACE ---
st.header("🧠 HARIS NEURO-CORE")

# Fetch Chat History
past_msgs = manage_db("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp", (st.session_state.current_session,), True)
for r, c in past_msgs:
    with st.chat_message(r): st.markdown(c)

# User Input
u_input = st.chat_input("Ask about the file or anything...")

if u_input:
    # 1. User message display aur save karein
    with st.chat_message("user"): st.markdown(u_input)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", ("user@test.com", st.session_state.current_session, "user", u_input, time.time()))

    # 2. AI Response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            file_data = st.session_state.persistent_file_text
            
            if file_data:
                # Agar Image hai
                if isinstance(file_data, Image.Image):
                    res = st.session_state.neuro_engine.process_image(file_data, u_input)
                # Agar PDF/Text hai
                else:
                    res = st.session_state.neuro_engine.process_query(u_input, file_context=file_data)
            else:
                res = st.session_state.neuro_engine.process_query(u_input)
            
            st.markdown(res)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", ("user@test.com", st.session_state.current_session, "assistant", res, time.time()))
    
    st.rerun()

import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
import sqlite3, time, hashlib, PyPDF2, docx

# Database for Login & History
def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_core.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

manage_db('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
manage_db('CREATE TABLE IF NOT EXISTS chat_logs (email TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# Session States for Memory
if "auth" not in st.session_state: st.session_state.auth = False
if "file_mem" not in st.session_state: st.session_state.file_mem = None
if "file_name" not in st.session_state: st.session_state.file_name = None

# --- AUTH SYSTEM ---
if not st.session_state.auth:
    st.title("🧠 NEURO-CORE LOGIN")
    t1, t2 = st.tabs(["Login", "Signup"])
    with t1:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            hp = hashlib.sha256(p.encode()).hexdigest()
            if manage_db("SELECT * FROM users WHERE email=? AND password=?", (e, hp), True):
                st.session_state.auth = True
                st.session_state.user_email = e
                st.rerun()
            else: st.error("Invalid Login")
    with t2:
        ne = st.text_input("New Email")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            hp = hashlib.sha256(np.encode()).hexdigest()
            try:
                manage_db("INSERT INTO users VALUES (?, ?)", (ne, hp))
                st.success("Account Created!")
            except: st.error("User already exists.")
    st.stop()

# --- MAIN INTERFACE ---
# APKI GROQ KEY YAHA HAI
API_KEY = "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"

if "engine" not in st.session_state:
    st.session_state.engine = NeuroCoreEngine(API_KEY)

st.title("🧠 HARIS NEURO-CORE")

# Sidebar for Uploads (Gemini Style)
with st.sidebar:
    st.header("📁 Data Lab")
    up_file = st.file_uploader("Upload PDF, Doc, or Image", type=['pdf','docx','png','jpg','jpeg'])
    
    if up_file and up_file.name != st.session_state.file_name:
        st.session_state.file_name = up_file.name
        with st.spinner("Extracting Knowledge..."):
            if up_file.type.startswith("image/"):
                st.session_state.file_mem = Image.open(up_file)
            else:
                if up_file.name.endswith('.pdf'):
                    pdf = PyPDF2.PdfReader(up_file); st.session_state.file_mem = " ".join([p.extract_text() for p in pdf.pages])
                elif up_file.name.endswith('.docx'):
                    doc = docx.Document(up_file); st.session_state.file_mem = " ".join([p.text for p in doc.paragraphs])
        st.sidebar.success(f"Loaded: {up_file.name}")

    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# Show History
logs = manage_db("SELECT role, content FROM chat_logs WHERE email=? ORDER BY timestamp", (st.session_state.user_email,), True)
for r, c in logs:
    with st.chat_message(r): st.markdown(c)

# Chat Input
prompt = st.chat_input("Ask me about the file or the world...")

if prompt:
    with st.chat_message("user"): st.markdown(prompt)
    manage_db("INSERT INTO chat_logs VALUES (?, ?, ?, ?)", (st.session_state.user_email, "user", prompt, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Neural Processing..."):
            ctx = st.session_state.file_mem
            # Chat history for memory
            hist = "\n".join([f"{l[0]}: {l[1]}" for l in logs[-5:]])
            
            if isinstance(ctx, Image.Image):
                res = st.session_state.engine.process_image(ctx, prompt)
            else:
                res = st.session_state.engine.process_query(prompt, file_context=ctx, history_context=hist)
            
            st.markdown(res)
            manage_db("INSERT INTO chat_logs VALUES (?, ?, ?, ?)", (st.session_state.user_email, "assistant", res, time.time()))

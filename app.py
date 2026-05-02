import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3
import time
import hashlib
import PyPDF2
import docx
from io import BytesIO

# --- DATABASE & SECURITY ---
def init_db():
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')
    conn.commit()
    conn.close()

def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    result = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return result

def extract_file_text(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in pdf_reader.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.txt'):
            return str(uploaded_file.read(), "utf-8")
        return None
    except: return "Error: Could not read file content."

init_db()
st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

if "reset_key" not in st.session_state: st.session_state.reset_key = 0

# --- AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1:
        e_l = st.text_input("Email")
        p_l = st.text_input("Password", type="password")
        if st.button("Login"):
            res = manage_db("SELECT * FROM users WHERE email=? AND password=?", (e_l, hashlib.sha256(p_l.encode()).hexdigest()), True)
            if res:
                st.session_state.update({"authenticated": True, "user_email": e_l, "current_session": f"Chat_{int(time.time())}"})
                st.rerun()
            else: st.error("Invalid credentials")
    with t2:
        e_s = st.text_input("Email", key="se")
        p_s = st.text_input("Password", type="password", key="sp")
        if st.button("Sign Up"):
            try:
                manage_db("INSERT INTO users VALUES (?, ?)", (e_s, hashlib.sha256(p_s.encode()).hexdigest()))
                st.success("Account created!")
            except: st.error("User already exists")
    st.stop()

# --- ENGINE ---
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.rerun()
    
    st.divider()
    st.subheader("Chat History")
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    
    for s in sessions:
        sid = s[0]
        col1, col2 = st.columns([4, 1])
        if col1.button(f"💬 {sid[:15]}...", key=sid, use_container_width=True):
            st.session_state.current_session = sid
            st.rerun()
        if col2.button("🗑️", key=f"del_{sid}"):
            manage_db("DELETE FROM messages WHERE session_id=?", (sid,))
            st.rerun()

    st.divider()
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

# --- MAIN UI ---
st.header("🧠 Neural Interface")
history = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)

for role, content in history:
    with st.chat_message(role): st.markdown(content)

# File & Input Section
with st.container():
    with st.expander("➕ Attach Files (PDF, DOCX, JPG, PNG, TXT)"):
        up_file = st.file_uploader("Choose a file", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"up_{st.session_state.reset_key}")

    c_mic, c_input = st.columns([1, 15])
    with c_mic: 
        audio = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=f"mic_{st.session_state.reset_key}")
    
    user_in = st.chat_input("Ask Haris Neuro-Core...")

prompt = audio['text'] if audio and audio['text'] else user_in

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
        if up_file: st.caption(f"📎 Attached: {up_file.name}")
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", prompt, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            if up_file:
                if up_file.type.startswith("image/"):
                    response = st.session_state.neuro_engine.process_image(Image.open(up_file), prompt)
                else:
                    text_content = extract_file_text(up_file)
                    response = st.session_state.neuro_engine.process_query(f"File Context: {text_content}\n\nUser Question: {prompt}")
            else:
                response = st.session_state.neuro_engine.process_query(prompt)
            
            st.markdown(response)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", response, time.time()))
    
    st.session_state.reset_key += 1
    st.rerun()

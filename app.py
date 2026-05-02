import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3
import time
import PyPDF2
import docx
import hashlib

# --- DATABASE & SECURITY ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')
    conn.commit()
    conn.close()

def manage_user(email, password, mode="login"):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    hashed = hash_password(password)
    if mode == "signup":
        try:
            c.execute("INSERT INTO users VALUES (?, ?)", (email, hashed))
            conn.commit()
            return True, "Account created!"
        except: return False, "Email already exists!"
    else:
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hashed))
        return (True, "Logged in!") if c.fetchone() else (False, "Invalid credentials!")

def save_to_db(email, session_id, role, content):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (email, session_id, role, content, time.time()))
    conn.commit()
    conn.close()

def load_session_history(email, session_id):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (email, session_id))
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in data]

def extract_doc_text(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            return " ".join([p.text for p in doc.paragraphs])
        return str(uploaded_file.read(), "utf-8")
    except: return "Error reading file."

init_db()
st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# --- LOGIN SYSTEM ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1:
        e_l = st.text_input("Email", key="l_e")
        p_l = st.text_input("Password", type="password", key="l_p")
        if st.button("Login"):
            success, msg = manage_user(e_l, p_l, "login")
            if success:
                st.session_state.update({"authenticated": True, "user_email": e_l, "current_session": f"Chat_{int(time.time())}"})
                st.rerun()
            else: st.error(msg)
    with t2:
        e_s = st.text_input("Email", key="s_e")
        p_s = st.text_input("Create Password", type="password", key="s_p")
        if st.button("Sign Up"):
            if "@" in e_s:
                success, msg = manage_user(e_s, p_s, "signup")
                if success: st.success(msg)
                else: st.error(msg)
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
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- MAIN CHAT ---
st.header("🧠 Neural Interface")
history = load_session_history(st.session_state.user_email, st.session_state.current_session)
for m in history:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Plus Button Expander (Gemini Style)
with st.expander("➕ Attach Multimedia / Take Photo"):
    col1, col2 = st.columns(2)
    up_file = col1.file_uploader("Upload File/Image", type=['png','jpg','jpeg','pdf','docx'], key="file_input")
    cam_file = col2.camera_input("Visual Sensor", key="cam_input")

# Input Bar
col_m, col_i = st.columns([1, 15])
with col_m: audio = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="voice")
user_in = st.chat_input("Ask Haris Neuro-Core...")

prompt = audio['text'] if audio and audio['text'] else user_in

if prompt:
    # Handle File & Camera Logic
    file_payload = cam_file if cam_file else up_file
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if file_payload: st.caption(f"Attached: {file_payload.name}")
    save_to_db(st.session_state.user_email, st.session_state.current_session, "user", prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            if file_payload and file_payload.type.startswith("image/"):
                img = Image.open(file_payload)
                response = st.session_state.neuro_engine.process_image(img, prompt)
            elif file_payload: # Document
                doc_text = extract_doc_text(file_payload)
                response = st.session_state.neuro_engine.process_query(f"Context: {doc_text[:3000]}\n\nUser: {prompt}")
            else:
                response = st.session_state.neuro_engine.process_query(prompt)
            
            st.markdown(response)
            save_to_db(st.session_state.user_email, st.session_state.current_session, "assistant", response)

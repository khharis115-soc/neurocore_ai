import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3
import time
import hashlib
import PyPDF2
import docx

# --- DATABASE ---
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
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

init_db()
st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

if "reset_key" not in st.session_state: st.session_state.reset_key = 0

# --- AUTH ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1:
        e_l = st.text_input("Email", key="login_email")
        p_l = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = manage_db("SELECT * FROM users WHERE email=? AND password=?", (e_l, hashlib.sha256(p_l.encode()).hexdigest()), True)
            if user:
                st.session_state.update({"authenticated": True, "user_email": e_l, "current_session": f"Chat_{int(time.time())}"})
                st.rerun()
            else: st.error("Wrong details")
    with t2:
        e_s = st.text_input("Email", key="reg_email")
        p_s = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            try:
                manage_db("INSERT INTO users VALUES (?, ?)", (e_s, hashlib.sha256(p_s.encode()).hexdigest()))
                st.success("User Registered!")
            except: st.error("Email already exists")
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
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    for s in sessions:
        sid = s[0]
        col_c, col_d = st.columns([4, 1])
        if col_c.button(f"💬 {sid[:15]}", key=sid, use_container_width=True):
            st.session_state.current_session = sid
            st.rerun()
        if col_d.button("🗑️", key=f"del_{sid}"):
            manage_db("DELETE FROM messages WHERE session_id=?", (sid,))
            st.rerun()
    st.divider()
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

# --- CHAT ---
st.header("🧠 Neural Interface")
messages = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for r, c in messages:
    with st.chat_message(r): st.markdown(c)

with st.container():
    with st.expander("➕ Attach Media / Files"):
        up_file = st.file_uploader("Upload", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"file_{st.session_state.reset_key}")

    col_mic, col_in = st.columns([1, 15])
    with col_mic:
        # Mic recorder with unique key to prevent stuck state
        audio = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=f"mic_{st.session_state.reset_key}")
    
    user_in = st.chat_input("Message HARIS NEURO-CORE...")

prompt = audio['text'] if audio and audio['text'] else user_in

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", prompt, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            if up_file and up_file.type.startswith("image/"):
                response = st.session_state.neuro_engine.process_image(Image.open(up_file), prompt)
            else:
                response = st.session_state.neuro_engine.process_query(prompt)
            st.markdown(response)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", response, time.time()))
    
    st.session_state.reset_key += 1
    st.rerun()

import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder, speech_to_text
import sqlite3, time, hashlib, PyPDF2, docx

# --- DATABASE LOGIC ---
def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

# Create tables for multi-device sync
manage_db('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
manage_db('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# --- AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    t1, t2 = st.tabs(["Login", "Signup"])
    
    with t1:
        le = st.text_input("Email", key="le")
        lp = st.text_input("Password", type="password", key="lp")
        if st.button("Login"):
            hp = hashlib.sha256(lp.encode()).hexdigest()
            user = manage_db("SELECT * FROM users WHERE email=? AND password=?", (le, hp), True)
            if user:
                st.session_state.update({"authenticated": True, "user_email": le, "current_session": f"Chat_{int(time.time())}", "reset_key": 0})
                st.rerun()
            else: st.error("Invalid credentials.")
            
    with t2:
        re = st.text_input("Email", key="re")
        rp = st.text_input("Password", type="password", key="rp")
        if st.button("Register"):
            try:
                rhp = hashlib.sha256(rp.encode()).hexdigest()
                manage_db("INSERT INTO users VALUES (?, ?)", (re, rhp))
                st.success("Account created! Now login.")
            except: st.error("User already exists.")
    st.stop()

# --- INITIALIZE CORE ---
# Your provided API Key
API_KEY = "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"

if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=API_KEY)

# --- SIDEBAR & SYNCED HISTORY ---
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    st.caption(f"Logged in: {st.session_state.user_email}")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.rerun()
    st.divider()
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    for s in sessions:
        if st.button(f"💬 {s[0][:18]}", key=s[0], use_container_width=True):
            st.session_state.current_session = s[0]
            st.rerun()
    if st.button("Logout"):
        st.session_state.clear(); st.rerun()

# --- CHAT INTERFACE ---
st.header("🧠 Neural Interface")
history = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for r, c in history:
    with st.chat_message(r): st.markdown(c)

st.divider()
with st.container():
    with st.expander("📎 Multimedia Options (Click to expand)"):
        up_file = st.file_uploader("Upload Media", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"f_{st.session_state.reset_key}")
    
    col_v, col_t = st.columns([1, 6])
    with col_v:
        # WhatsApp style mic logic
        v_text = speech_to_text(language='en', start_prompt="🎤", stop_prompt="🛑", key=f"v_{st.session_state.reset_key}")
    with col_t:
        u_msg = st.chat_input("Message HARIS NEURO-CORE...")

final_prompt = v_text if v_text else u_msg

if final_prompt:
    # Save User Msg
    with st.chat_message("user"): st.markdown(final_prompt)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_prompt, time.time()))

    # Response Logic
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                if up_file:
                    if up_file.type.startswith("image/"):
                        res = st.session_state.neuro_engine.process_image(Image.open(up_file), final_prompt)
                    else:
                        txt = ""
                        if up_file.name.endswith('.pdf'):
                            pdf = PyPDF2.PdfReader(up_file); txt = " ".join([p.extract_text() for p in pdf.pages])
                        elif up_file.name.endswith('.docx'):
                            doc = docx.Document(up_file); txt = " ".join([p.text for p in doc.paragraphs])
                        else: txt = up_file.read().decode()
                        res = st.session_state.neuro_engine.process_query(final_prompt, file_context=txt)
                else:
                    res = st.session_state.neuro_engine.process_query(final_prompt)
                
                st.markdown(res)
                manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", res, time.time()))
            except Exception as e:
                st.error(f"Neural Failure: {e}")

    st.session_state.reset_key += 1
    st.rerun()

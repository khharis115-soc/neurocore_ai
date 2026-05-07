import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder, speech_to_text
import sqlite3, time, hashlib, PyPDF2, docx

# --- DATABASE SETUP ---
def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

# Initialize tables
manage_db('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
manage_db('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# --- AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    tab1, tab2 = st.tabs(["Login", "Signup"])
    with tab1:
        le = st.text_input("Email", key="login_email")
        lp = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            hashed_p = hashlib.sha256(lp.encode()).hexdigest()
            user = manage_db("SELECT * FROM users WHERE email=? AND password=?", (le, hashed_p), True)
            if user:
                st.session_state.update({"authenticated": True, "user_email": le, "current_session": f"Chat_{int(time.time())}", "reset_key": 0})
                st.rerun()
            else: st.error("Wrong email or password.")
    with tab2:
        re = st.text_input("New Email", key="reg_email")
        rp = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Create Account"):
            try:
                hashed_rp = hashlib.sha256(rp.encode()).hexdigest()
                manage_db("INSERT INTO users VALUES (?, ?)", (re, hashed_rp))
                st.success("Signup successful! Please login.")
            except: st.error("Email already registered.")
    st.stop()

# --- ENGINE CONFIG ---
API_KEY = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=API_KEY)

# --- SIDEBAR & CHAT HISTORY SYNC ---
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    st.write(f"User: {st.session_state.user_email}")
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

# --- MAIN INTERFACE ---
st.header("🧠 Neural Interface")

# Fetch context history (last 10 messages) for the AI's memory
past_data = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp DESC LIMIT 10", (st.session_state.user_email, st.session_state.current_session), True)
history_str = "\n".join([f"{m[0]}: {m[1]}" for m in reversed(past_data)])

# Show full history on screen
history = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for r, c in history:
    with st.chat_message(r): st.markdown(c)

# Input Section
st.divider()
with st.container():
    with st.expander("📎 Attach Media/Docs"):
        up_file = st.file_uploader("Upload", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"file_{st.session_state.reset_key}")
    
    col_v, col_t = st.columns([1, 6])
    with col_v:
        # Fixed mic logic - no more KeyError
        v_text = speech_to_text(language='en', start_prompt="🎤", stop_prompt="🛑", key=f"mic_{st.session_state.reset_key}")
    with col_t:
        u_msg = st.chat_input("Message Haris Neuro-Core...")

# Final Logic
final_prompt = v_text if v_text else u_msg

if final_prompt:
    with st.chat_message("user"): st.markdown(final_prompt)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_prompt, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Analyzing context..."):
            if up_file:
                if up_file.type.startswith("image/"):
                    res = st.session_state.neuro_engine.process_image(Image.open(up_file), final_prompt, history_context=history_str)
                else:
                    raw_text = ""
                    if up_file.name.endswith('.pdf'):
                        pdf = PyPDF2.PdfReader(up_file); raw_text = " ".join([p.extract_text() for p in pdf.pages])
                    elif up_file.name.endswith('.docx'):
                        doc = docx.Document(up_file); raw_text = " ".join([p.text for p in doc.paragraphs])
                    res = st.session_state.neuro_engine.process_query(final_prompt, file_context=raw_text, history_context=history_str)
            else:
                res = st.session_state.neuro_engine.process_query(final_prompt, history_context=history_str)
            
            st.markdown(res)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", res, time.time()))

    st.session_state.reset_key += 1
    st.rerun()

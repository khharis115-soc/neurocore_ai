import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder, speech_to_text
import sqlite3, time, hashlib, PyPDF2, docx

# DB Logic
def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

manage_db('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
manage_db('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# --- IMPORTANT: SESSION STATE FOR PDF PERSISTENCE ---
if "current_file_content" not in st.session_state:
    st.session_state.current_file_content = None
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = None

# Auth Section
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    t1, t2 = st.tabs(["Login", "Signup"])
    with t1:
        e, p = st.text_input("Email"), st.text_input("Password", type="password")
        if st.button("Login"):
            hp = hashlib.sha256(p.encode()).hexdigest()
            if manage_db("SELECT * FROM users WHERE email=? AND password=?", (e, hp), True):
                st.session_state.update({"authenticated": True, "user_email": e, "current_session": f"Chat_{int(time.time())}", "reset_key": 0})
                st.rerun()
    with t2:
        re, rp = st.text_input("New Email"), st.text_input("New Password", type="password")
        if st.button("Register"):
            try: manage_db("INSERT INTO users VALUES (?, ?)", (re, hashlib.sha256(rp.encode()).hexdigest())); st.success("Created!")
            except: st.error("Error")
    st.stop()

# Initialize Engine
API_KEY = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=API_KEY)

# Sidebar
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat"):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.session_state.current_file_content = None # New chat resets file
        st.session_state.current_file_name = None
        st.rerun()
    st.divider()
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    for s in sessions:
        if st.button(f"💬 {s[0][:15]}", key=s[0]):
            st.session_state.current_session = s[0]; st.rerun()

# Main UI
st.header("🧠 Neural Interface")

# Memory Context (History)
past = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp DESC LIMIT 12", (st.session_state.user_email, st.session_state.current_session), True)
history_str = "\n".join([f"{m[0]}: {m[1]}" for m in reversed(past)])

# Display Chat History
full_chat = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for r, c in full_chat:
    with st.chat_message(r): st.markdown(c)

# Input with Persistence
with st.container():
    up_file = st.file_uploader("Attach PDF/Doc/Image", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"f_{st.session_state.reset_key}")
    
    # Check if new file is uploaded and save to Session State
    if up_file and up_file.name != st.session_state.current_file_name:
        st.session_state.current_file_name = up_file.name
        with st.spinner("Neural extraction in progress..."):
            if up_file.type.startswith("image/"):
                st.session_state.current_file_content = Image.open(up_file)
            else:
                raw_text = ""
                if up_file.name.endswith('.pdf'):
                    pdf = PyPDF2.PdfReader(up_file); raw_text = " ".join([p.extract_text() for p in pdf.pages])
                elif up_file.name.endswith('.docx'):
                    doc = docx.Document(up_file); raw_text = " ".join([p.text for p in doc.paragraphs])
                else: raw_text = up_file.read().decode()
                st.session_state.current_file_content = raw_text

    c1, c2 = st.columns([1, 6])
    with c1:
        v_text = speech_to_text(language='en', start_prompt="🎤", stop_prompt="🛑", key=f"v_{st.session_state.reset_key}")
    with c2:
        u_msg = st.chat_input("Ask HARIS NEURO-CORE...")

final_prompt = v_text if v_text else u_msg

if final_prompt:
    with st.chat_message("user"): st.markdown(final_prompt)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_prompt, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            # Use Session State content instead of up_file
            content = st.session_state.current_file_content
            if content:
                if isinstance(content, Image.Image):
                    res = st.session_state.neuro_engine.process_image(content, final_prompt, history_context=history_str)
                else:
                    res = st.session_state.neuro_engine.process_query(final_prompt, file_context=content, history_context=history_str)
            else:
                res = st.session_state.neuro_engine.process_query(final_prompt, history_context=history_str)
            
            st.markdown(res)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", res, time.time()))
    
    st.session_state.reset_key += 1
    st.rerun()

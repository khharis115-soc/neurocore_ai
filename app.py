import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3, time, hashlib, PyPDF2, docx

# --- DB SETUP ---
def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

# Create tables if not exist
manage_db('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
manage_db('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# --- AUTH LOGIC ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            u = manage_db("SELECT * FROM users WHERE email=? AND password=?", (e, hashlib.sha256(p.encode()).hexdigest()), True)
            if u:
                st.session_state.update({"authenticated": True, "user_email": e, "current_session": f"Chat_{int(time.time())}", "reset_key": 0})
                st.rerun()
    if not st.session_state.get("authenticated"): st.stop()

# --- ENGINE & UI ---
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key="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")

with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.rerun()
    st.divider()
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    for s in sessions:
        col1, col2 = st.columns([4, 1])
        if col1.button(f"💬 {s[0][:15]}", key=s[0], use_container_width=True):
            st.session_state.current_session = s[0]
            st.rerun()
        if col2.button("🗑️", key=f"del_{s[0]}"):
            manage_db("DELETE FROM messages WHERE session_id=?", (s[0],))
            st.rerun()

# Display Chat
st.header("🧠 Neural Interface")
history = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for r, c in history:
    with st.chat_message(r): st.markdown(c)

# --- INPUT AREA (GEMINI STYLE) ---
with st.container():
    with st.expander("📎 Attach Files (PDF, DOCX, Images)"):
        up_file = st.file_uploader("Upload", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"file_{st.session_state.reset_key}")
    
    c_mic, c_in = st.columns([1, 15])
    with c_mic:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=f"mic_{st.session_state.reset_key}")
    
    user_msg = st.chat_input("Ask anything...")

# Process Input
final_input = None
if audio and isinstance(audio, dict) and audio.get('text'):
    final_input = audio['text']
elif user_msg:
    final_input = user_msg

if final_input:
    # Save & Show User Message
    with st.chat_message("user"):
        st.markdown(final_input)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_input, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if up_file:
                if up_file.type.startswith("image/"):
                    response = st.session_state.neuro_engine.process_image(Image.open(up_file), final_input)
                else:
                    # Document extraction
                    text = ""
                    if up_file.name.endswith('.pdf'):
                        reader = PyPDF2.PdfReader(up_file)
                        text = " ".join([p.extract_text() for p in reader.pages])
                    elif up_file.name.endswith('.docx'):
                        doc = docx.Document(up_file)
                        text = " ".join([p.text for p in doc.paragraphs])
                    else:
                        text = up_file.read().decode()
                    response = st.session_state.neuro_engine.process_query(final_input, file_context=text)
            else:
                response = st.session_state.neuro_engine.process_query(final_input)
            
            st.markdown(response)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", response, time.time()))
    
    st.session_state.reset_key += 1
    st.rerun()

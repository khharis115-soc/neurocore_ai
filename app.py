import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3, time, hashlib, PyPDF2, docx

# --- DATABASE MANAGEMENT ---
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

# --- AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        e = st.text_input("Email", key="l_email")
        p = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login"):
            u = manage_db("SELECT * FROM users WHERE email=? AND password=?", (e, hashlib.sha256(p.encode()).hexdigest()), True)
            if u:
                st.session_state.update({"authenticated": True, "user_email": e, "current_session": f"Chat_{int(time.time())}", "reset_key": 0})
                st.rerun()
    with tab2:
        re = st.text_input("Email", key="r_email")
        rp = st.text_input("Password", type="password", key="r_pass")
        if st.button("Register"):
            try:
                manage_db("INSERT INTO users VALUES (?, ?)", (re, hashlib.sha256(rp.encode()).hexdigest()))
                st.success("Registration Successful!")
            except: st.error("Email already exists.")
    st.stop()

# --- INITIALIZE ENGINE ---
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key="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")

# --- SIDEBAR & HISTORY ---
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.rerun()
    st.divider()
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    for s in sessions:
        c1, c2 = st.columns([4, 1])
        if c1.button(f"💬 {s[0][:15]}", key=s[0], use_container_width=True):
            st.session_state.current_session = s[0]
            st.rerun()
        if c2.button("🗑️", key=f"del_{s[0]}"):
            manage_db("DELETE FROM messages WHERE session_id=?", (s[0],))
            st.rerun()
    st.divider()
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- MAIN CHAT INTERFACE ---
st.header("🧠 Neural Interface")
history = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for role, text in history:
    with st.chat_message(role): st.markdown(text)

# --- INPUT SECTION (The Fix) ---
st.divider()
with st.container():
    with st.expander("📎 Attach Documents or Images"):
        up_file = st.file_uploader("Upload File", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"file_{st.session_state.reset_key}")
    
    col_mic, col_txt = st.columns([2, 10])
    with col_mic:
        # WhatsApp Style Recording
        audio_data = mic_recorder(start_prompt="🎤 Start", stop_prompt="🛑 Send", key=f"mic_{st.session_state.reset_key}")
    
    with col_txt:
        user_msg = st.chat_input("Type your message...")

# --- LOGIC HANDLING ---
final_query = None
if audio_data and audio_data.get('text'):
    final_query = audio_data['text']
elif user_msg:
    final_query = user_msg

if final_query:
    # Save User Entry
    with st.chat_message("user"):
        st.markdown(final_query)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_query, time.time()))

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                if up_file:
                    if up_file.type.startswith("image/"):
                        resp = st.session_state.neuro_engine.process_image(Image.open(up_file), final_query)
                    else:
                        # Extract Document Text
                        raw_text = ""
                        if up_file.name.endswith('.pdf'):
                            pdf = PyPDF2.PdfReader(up_file)
                            raw_text = " ".join([page.extract_text() for page in pdf.pages])
                        elif up_file.name.endswith('.docx'):
                            doc = docx.Document(up_file)
                            raw_text = " ".join([p.text for p in doc.paragraphs])
                        else:
                            raw_text = up_file.read().decode()
                        resp = st.session_state.neuro_engine.process_query(final_query, file_context=raw_text)
                else:
                    resp = st.session_state.neuro_engine.process_query(final_query)
                
                st.markdown(resp)
                manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", resp, time.time()))
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.session_state.reset_key += 1
    st.rerun()

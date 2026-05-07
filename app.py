import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder, speech_to_text
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

manage_db('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
manage_db('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# Auth Logic
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
            try: 
                manage_db("INSERT INTO users VALUES (?, ?)", (re, hashlib.sha256(rp.encode()).hexdigest()))
                st.success("User Registered!")
            except: st.error("User already exists.")
    st.stop()

# Initialize Engine with your NEW key
API_KEY = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=API_KEY)

# Sidebar
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat"):
        st.session_state.current_session = f"Chat_{int(time.time())}"; st.rerun()
    st.divider()
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    for s in sessions:
        if st.button(f"💬 {s[0][:15]}", key=s[0]):
            st.session_state.current_session = s[0]; st.rerun()

# Main UI
st.header("🧠 Neural Interface")

# Context for Memory (Last 12 messages)
past_msgs = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp DESC LIMIT 12", (st.session_state.user_email, st.session_state.current_session), True)
history_str = "\n".join([f"{m[0]}: {m[1]}" for m in reversed(past_msgs)])

# Display full current session
full_chat = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for r, c in full_chat:
    with st.chat_message(r): st.markdown(c)

# Inputs
with st.container():
    up_file = st.file_uploader("Attach PDF/Doc/Image", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"f_{st.session_state.reset_key}")
    c1, c2 = st.columns([1, 6])
    with c1:
        v_text = speech_to_text(language='en', start_prompt="🎤", stop_prompt="🛑", key=f"v_{st.session_state.reset_key}")
    with c2:
        u_msg = st.chat_input("Ask HARIS NEURO-CORE anything...")

final_prompt = v_text if v_text else u_msg

if final_prompt:
    with st.chat_message("user"): st.markdown(final_prompt)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_prompt, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Processing context..."):
            res = ""
            if up_file:
                if up_file.type.startswith("image/"):
                    res = st.session_state.neuro_engine.process_image(Image.open(up_file), final_prompt, history_context=history_str)
                else:
                    extracted_text = ""
                    if up_file.name.endswith('.pdf'):
                        pdf_reader = PyPDF2.PdfReader(up_file)
                        extracted_text = " ".join([page.extract_text() for page in pdf_reader.pages])
                    elif up_file.name.endswith('.docx'):
                        doc = docx.Document(up_file)
                        extracted_text = " ".join([p.text for p in doc.paragraphs])
                    else:
                        extracted_text = up_file.read().decode()
                    
                    # Passing extracted text to query engine
                    res = st.session_state.neuro_engine.process_query(final_prompt, file_context=extracted_text, history_context=history_str)
            else:
                res = st.session_state.neuro_engine.process_query(final_prompt, history_context=history_str)
            
            st.markdown(res)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", res, time.time()))
    
    st.session_state.reset_key += 1
    st.rerun()

import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3
import time
import PyPDF2
import docx

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)''')
    conn.commit()
    conn.close()

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

def get_all_sessions(email):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (email,))
    sessions = [row[0] for row in c.fetchall()]
    conn.close()
    return sessions

init_db()

st.set_page_config(page_title="HARIS NEURO-CORE", page_icon="🧠", layout="wide")

# --- AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🧠 HARIS NEURO-CORE</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email_input = st.text_input("Enter Email to access history")
        if st.button("🌐 Continue with Google"):
            if "@" in email_input:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email_input
                st.session_state["current_session"] = f"Chat_{int(time.time())}"
                st.rerun()
    st.stop()

# Engine Init
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- SIDEBAR (History) ---
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state["current_session"] = f"Chat_{int(time.time())}"
        st.rerun()
    
    st.divider()
    st.subheader("Recent Conversations")
    past_sessions = get_all_sessions(st.session_state.user_email)
    for s_id in past_sessions:
        if st.button(f"💬 {s_id[:20]}...", key=f"btn_{s_id}", use_container_width=True):
            st.session_state["current_session"] = s_id
            st.rerun()

# --- MAIN INTERFACE ---
st.header("🧠 Neural Interface")

# Display Messages
chat_history = load_session_history(st.session_state.user_email, st.session_state.current_session)
for msg in chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Gemini Style Input Section
st.write("---")
with st.container():
    # Plus Icon for Files/Camera
    with st.expander("➕ Add Multimedia (Image/Doc/Camera)"):
        col_f, col_c = st.columns(2)
        with col_f:
            uploaded_file = st.file_uploader("Upload Image, PDF, or DOCX", type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'txt'])
        with col_c:
            camera_photo = st.camera_input("Visual Sensor")

    # Voice and Text Input
    col_mic, col_in = st.columns([1, 15])
    with col_mic:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic")
    with col_in:
        user_query = st.chat_input("Ask Haris Neuro-Core...")

prompt = audio['text'] if audio and audio['text'] else user_query

if prompt:
    with st.chat_message("user"): st.markdown(prompt)
    save_to_db(st.session_state.user_email, st.session_state.current_session, "user", prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            img = None
            if camera_photo: img = Image.open(camera_photo)
            elif uploaded_file and uploaded_file.type.startswith("image/"): img = Image.open(uploaded_file)
            
            if img:
                st.image(img, width=250)
                response = st.session_state.neuro_engine.process_image(img, prompt)
            else:
                # Text/Doc processing logic
                response = st.session_state.neuro_engine.process_query(prompt)
            
            st.markdown(response)
            save_to_db(st.session_state.user_email, st.session_state.current_session, "assistant", response)

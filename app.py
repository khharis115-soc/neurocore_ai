import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3
import time

# --- DATABASE SETUP ---
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
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", 
              (email, session_id, role, content, time.time()))
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

# Page Config
st.set_page_config(page_title="HARIS NEURO-CORE", page_icon="🧠", layout="wide")

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🧠 HARIS NEURO-CORE</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email_input = st.text_input("Enter Email")
        if st.button("🌐 Continue with Google"):
            if "@" in email_input:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email_input
                # Default session for new login
                st.session_state["current_session"] = f"Chat_{int(time.time())}"
                st.rerun()
    st.stop()

# Engine Setup
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- SIDEBAR (HISTORY & NEW CHAT) ---
with st.sidebar:
    st.title("🧠 HARIS NEURO-CORE")
    
    # 1. NEW CHAT BUTTON
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state["current_session"] = f"Chat_{int(time.time())}"
        st.rerun()
    
    st.divider()
    
    # 2. SIDEBAR HISTORY LINKS
    st.subheader("Recent Chats")
    past_sessions = get_all_sessions(st.session_state.user_email)
    
    if not past_sessions:
        st.info("No history yet.")
    
    for s_id in past_sessions:
        # Har purani chat ka link yahan banega
        if st.button(f"💬 {s_id}", key=f"btn_{s_id}", use_container_width=True):
            st.session_state["current_session"] = s_id
            st.rerun()

    st.divider()
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

# --- MAIN CHAT AREA ---
st.header("🧠 Neural Interface")
st.caption(f"Logged in: {st.session_state.user_email} | Session: {st.session_state.current_session}")

# Load current session messages
current_messages = load_session_history(st.session_state.user_email, st.session_state.current_session)

# Display history
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Logic
audio = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="voice")
user_query = st.chat_input("Ask HARIS NEURO-CORE...")

prompt = None
if audio and audio['text']:
    prompt = audio['text']
elif user_query:
    prompt = user_query

if prompt:
    # Display & Save User Input
    with st.chat_message("user"):
        st.markdown(prompt)
    save_to_db(st.session_state.user_email, st.session_state.current_session, "user", prompt)
    
    with st.chat_message("assistant"):
        # Image Processing (optional in sidebar)
        camera_photo = st.sidebar.camera_input("Visual Sensor", key="cam_sensor")
        if camera_photo:
            img = Image.open(camera_photo)
            response = st.session_state.neuro_engine.process_image(img, prompt)
        else:
            response = st.session_state.neuro_engine.process_query(prompt)
        
        st.markdown(response)
        # Save Assistant Response
        save_to_db(st.session_state.user_email, st.session_state.current_session, "assistant", response)

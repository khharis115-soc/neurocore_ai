import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3
import time
import PyPDF2
import docx
import hashlib

# --- DATABASE & SECURITY LOGIC ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT)''')
    # Messages Table
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)''')
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
        except:
            return False, "Email already exists!"
    else:
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hashed))
        if c.fetchone():
            return True, "Logged in!"
        return False, "Invalid email or password!"

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

# --- AUTHENTICATION INTERFACE ---
if "authenticated" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🧠 HARIS NEURO-CORE</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        e_login = st.text_input("Email", key="l_email")
        p_login = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login"):
            success, msg = manage_user(e_login, p_login, "login")
            if success:
                st.session_state.authenticated = True
                st.session_state.user_email = e_login
                st.session_state.current_session = f"Chat_{int(time.time())}"
                st.rerun()
            else: st.error(msg)
            
    with tab2:
        e_signup = st.text_input("Email", key="s_email")
        p_signup = st.text_input("Create Password", type="password", key="s_pass")
        if st.button("Create Account"):
            if "@" in e_signup and len(p_signup) > 5:
                success, msg = manage_user(e_signup, p_signup, "signup")
                if success: st.success(msg)
                else: st.error(msg)
            else: st.warning("Enter valid email & password (min 6 chars)")
    st.stop()

# --- ENGINE & SIDEBAR ---
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.rerun()
    st.divider()
    st.subheader("Recent Chats")
    for s_id in get_all_sessions(st.session_state.user_email):
        if st.button(f"💬 {s_id[:20]}", key=s_id, use_container_width=True):
            st.session_state.current_session = s_id
            st.rerun()
    st.divider()
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

# --- MAIN CHAT ---
st.header("🧠 Neural Interface")
history = load_session_history(st.session_state.user_email, st.session_state.current_session)
for m in history:
    with st.chat_message(m["role"]): st.markdown(m["content"])

with st.container():
    with st.expander("➕ Add Multimedia (Image/Doc/Camera)"):
        col_f, col_c = st.columns(2)
        uploaded_file = col_f.file_uploader("Upload", type=['png','jpg','jpeg','pdf','docx'])
        camera_photo = col_c.camera_input("Visual Sensor")

    col_mic, col_in = st.columns([1, 15])
    with col_mic: audio = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic")
    user_query = st.chat_input("Ask Haris Neuro-Core...")

prompt = audio['text'] if audio and audio['text'] else user_query

if prompt:
    with st.chat_message("user"): st.markdown(prompt)
    save_to_db(st.session_state.user_email, st.session_state.current_session, "user", prompt)
    
    with st.chat_message("assistant"):
        img = None
        if camera_photo: img = Image.open(camera_photo)
        elif uploaded_file and uploaded_file.type.startswith("image/"): img = Image.open(uploaded_file)
        
        if img:
            st.image(img, width=250)
            response = st.session_state.neuro_engine.process_image(img, prompt)
        else:
            response = st.session_state.neuro_engine.process_query(prompt)
        
        st.markdown(response)
        save_to_db(st.session_state.user_email, st.session_state.current_session, "assistant", response)

import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3
import time
import PyPDF2
import docx
import io

# --- DOCUMENT PROCESSING ---
def extract_text(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            return " ".join([para.text for para in doc.paragraphs])
        elif uploaded_file.type == "text/plain":
            return str(uploaded_file.read(), "utf-8")
    except Exception as e:
        return f"Error extracting text: {str(e)}"
    return None

# --- DATABASE SETUP (Email History) ---
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

# Page Config
st.set_page_config(page_title="HARIS NEURO-CORE", page_icon="🧠", layout="wide")

# --- LOGIN SCREEN ---
if "authenticated" not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #00FFAA;'>🧠 HARIS NEURO-CORE</h1>", unsafe_allow_html=True)
    st.write("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("Neural Access Portal")
        email_input = st.text_input("Enter Email Address")
        if st.button("🌐 Continue with Google"):
            if "@" in email_input:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email_input
                st.session_state["current_session"] = f"Chat_{int(time.time())}"
                st.rerun()
            else:
                st.error("Please enter a valid email.")
    st.stop()

# Brain Setup
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- SIDEBAR (THE GEMINI EXPERIENCE) ---
with st.sidebar:
    st.title("🧠 HARIS NEURO-CORE")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state["current_session"] = f"Chat_{int(time.time())}"
        st.rerun()
    
    st.divider()
    st.subheader("🛠️ NEURO-LAB")
    uploaded_file = st.file_uploader("Analyze (PDF, DOCX, Image)", type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'txt'], key="lab_upload")
    camera_photo = st.camera_input("Visual Sensor", key="lab_cam")
    
    st.divider()
    st.subheader("Recent Conversations")
    past_sessions = get_all_sessions(st.session_state.user_email)
    if not past_sessions:
        st.caption("No history found.")
    for s_id in past_sessions:
        if st.button(f"💬 {s_id[:25]}", key=f"btn_{s_id}", use_container_width=True):
            st.session_state["current_session"] = s_id
            st.rerun()

    st.divider()
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

# --- MAIN CHAT AREA ---
st.header("🧠 Neural Interface")
st.caption(f"Session: {st.session_state.current_session}")

# Display current chat history
chat_history = load_session_history(st.session_state.user_email, st.session_state.current_session)
for msg in chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Logic (Voice + Text)
audio = mic_recorder(start_prompt="🎤 Speak to Core", stop_prompt="🛑 Stop", key="voice")
user_query = st.chat_input("Input command...")
prompt = audio['text'] if audio and audio['text'] else user_query

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    save_to_db(st.session_state.user_email, st.session_state.current_session, "user", prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            if uploaded_file:
                if uploaded_file.type.startswith("image/"):
                    img = Image.open(uploaded_file)
                    response = st.session_state.neuro_engine.process_image(img, prompt)
                else:
                    doc_text = extract_text(uploaded_file)
                    context_prompt = f"File Content: {doc_text[:3500]}\n\nQuestion: {prompt}"
                    response = st.session_state.neuro_engine.process_query(context_prompt)
            elif camera_photo:
                img = Image.open(camera_photo)
                response = st.session_state.neuro_engine.process_image(img, prompt)
            else:
                response = st.session_state.neuro_engine.process_query(prompt)
            
            st.markdown(response)
            save_to_db(st.session_state.user_email, st.session_state.current_session, "assistant", response)

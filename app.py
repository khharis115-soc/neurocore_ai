import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import sqlite3

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('neuro_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (email TEXT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_chat(email, role, content):
    conn = sqlite3.connect('neuro_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO history VALUES (?, ?, ?)", (email, role, content))
    conn.commit()
    conn.close()

def load_chat(email):
    conn = sqlite3.connect('neuro_history.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM history WHERE email=?", (email,))
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in data]

init_db()

# Page Config
st.set_page_config(page_title="HARIS NEURO-CORE", page_icon="🧠", layout="wide")

# --- LOGIN LOGIC ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE")
    st.subheader("🔐 Login to Access Your Saved History")
    
    email_input = st.text_input("Enter Email")
    user_input_name = st.text_input("Username")
    pas_input = st.text_input("Password", type="password")
    
    if st.button("Access Neural Core"):
        if user_input_name == "haris" and pas_input == "neuro2026" and "@" in email_input:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email_input
            # Load specific history for this email
            st.session_state["messages"] = load_chat(email_input)
            st.rerun()
        else:
            st.error("Invalid Credentials or Email Format")
    st.stop()

# Brain Setup
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ NEURO-LAB")
    st.write(f"User: `{st.session_state.user_email}`")
    if st.button("Logout"):
        del st.session_state["authenticated"]
        st.rerun()
    
    st.divider()
    st.subheader("🎤 Voice")
    audio = mic_recorder(start_prompt="Speak", stop_prompt="Stop", key="voice_mic")
    
    st.divider()
    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], key="file_up")
    camera_photo = st.camera_input("Sensor", key="neuro_cam")

# --- MAIN CHAT ---
st.header("🧠 HARIS NEURO-CORE")

# Display History from Database
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Input
prompt = None
if audio and audio['text']:
    prompt = audio['text']
elif input_text := st.chat_input("Message HARIS NEURO-CORE..."):
    prompt = input_text

if prompt:
    # Save & Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat(st.session_state.user_email, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        img = None
        if camera_photo: img = Image.open(camera_photo)
        elif uploaded_file: img = Image.open(uploaded_file)
        
        if img:
            st.image(img, width=300)
            response = st.session_state.neuro_engine.process_image(img, prompt)
        else:
            response = st.session_state.neuro_engine.process_query(prompt)
            
        st.markdown(response)
        
        # Save Assistant Message to DB
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat(st.session_state.user_email, "assistant", response)

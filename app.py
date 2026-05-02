import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder, speech_to_text
import sqlite3, time, hashlib, PyPDF2, docx

# --- DATABASE ---
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

# --- AUTH ---
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
    if not st.session_state.get("authenticated"): st.stop()

if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key="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")

# --- UI SIDEBAR ---
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.rerun()
    st.divider()
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- CHAT INTERFACE ---
st.header("🧠 Neural Interface")
history = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for role, text in history:
    with st.chat_message(role): st.markdown(text)

# --- VOICE & TEXT INPUT (GEMINI STYLE) ---
st.divider()
input_container = st.container()

with input_container:
    # 1. File Upload Expander
    with st.expander("📎 Attach Media"):
        up_file = st.file_uploader("Upload", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"file_{st.session_state.reset_key}")
    
    col_voice, col_text = st.columns([1, 5])
    
    with col_voice:
        # Yeh component direct text return karta hai jaise hi aap bolna band karte hain
        voice_text = speech_to_text(
            language='en', 
            start_prompt="🎤", 
            stop_prompt="🛑", 
            key=f"speech_{st.session_state.reset_key}"
        )
    
    with col_text:
        user_input = st.chat_input("Message NEURO-CORE...")

# --- RESPONSE LOGIC ---
# prioritize voice_text over manual type
final_query = voice_text if voice_text else user_input

if final_query:
    # Save & Show
    with st.chat_message("user"):
        st.markdown(final_query)
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_query, time.time()))

    # Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Processing voice..."):
            try:
                if up_file:
                    if up_file.type.startswith("image/"):
                        resp = st.session_state.neuro_engine.process_image(Image.open(up_file), final_query)
                    else:
                        # Document context
                        raw_text = ""
                        if up_file.name.endswith('.pdf'):
                            pdf = PyPDF2.PdfReader(up_file)
                            raw_text = " ".join([page.extract_text() for page in pdf.pages])
                        elif up_file.name.endswith('.docx'):
                            doc = docx.Document(up_file)
                            raw_text = " ".join([p.text for p in doc.paragraphs])
                        resp = st.session_state.neuro_engine.process_query(final_query, file_context=raw_text)
                else:
                    resp = st.session_state.neuro_engine.process_query(final_query)
                
                st.markdown(resp)
                manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", resp, time.time()))
            except Exception as e:
                st.error(f"Neural Error: {e}")
    
    st.session_state.reset_key += 1
    st.rerun()

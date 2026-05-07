import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder, speech_to_text
import sqlite3, time, hashlib, PyPDF2, docx

# --- GLOBAL DATABASE CONFIG ---
def manage_db(query, params=(), fetch=False):
    conn = sqlite3.connect('neuro_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

# Initialize tables (Email based chat isolation)
manage_db('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
manage_db('CREATE TABLE IF NOT EXISTS messages (email TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')

st.set_page_config(page_title="HARIS NEURO-CORE", layout="wide")

# --- AUTHENTICATION SYSTEM (Multi-Device Sync) ---
if "authenticated" not in st.session_state:
    st.title("🧠 HARIS NEURO-CORE: Global Sync")
    t1, t2 = st.tabs(["Login", "Create Global Account"])
    
    with t1:
        e = st.text_input("Email", key="l_email")
        p = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login & Sync"):
            hashed = hashlib.sha256(p.encode()).hexdigest()
            user = manage_db("SELECT * FROM users WHERE email=? AND password=?", (e, hashed), True)
            if user:
                # Login hone par user ka email session mein store ho jayega
                st.session_state.update({"authenticated": True, "user_email": e, "current_session": f"Chat_{int(time.time())}", "reset_key": 0})
                st.rerun()
            else: st.error("Account not found or wrong password.")
            
    with t2:
        re = st.text_input("Email", key="r_email")
        rp = st.text_input("Password", type="password", key="r_pass")
        if st.button("Signup"):
            try:
                hashed = hashlib.sha256(rp.encode()).hexdigest()
                manage_db("INSERT INTO users VALUES (?, ?)", (re, hashed))
                st.success("Account created! Now login to sync across devices.")
            except: st.error("Email already registered.")
    st.stop()

# --- INITIALIZE ENGINE ---
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key="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")

# --- SIDEBAR (History filtered by User Email) ---
with st.sidebar:
    st.title("🧠 NEURO-CORE")
    st.caption(f"Account: {st.session_state.user_email}")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session = f"Chat_{int(time.time())}"
        st.rerun()
    
    st.divider()
    st.subheader("Cloud History")
    # Sirf uss user ki chats dikhayega jo login hai
    sessions = manage_db("SELECT DISTINCT session_id FROM messages WHERE email=? ORDER BY timestamp DESC", (st.session_state.user_email,), True)
    for s in sessions:
        col_c, col_d = st.columns([4, 1])
        if col_c.button(f"💬 {s[0][:15]}", key=s[0], use_container_width=True):
            st.session_state.current_session = s[0]
            st.rerun()
        if col_d.button("🗑️", key=f"del_{s[0]}"):
            manage_db("DELETE FROM messages WHERE session_id=?", (s[0],))
            st.rerun()
    
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

# --- CHAT ENGINE ---
st.header("🧠 Neural Interface")
# History load karte waqt user email filter lagaya hai
history = manage_db("SELECT role, content FROM messages WHERE email=? AND session_id=? ORDER BY timestamp", (st.session_state.user_email, st.session_state.current_session), True)
for r, c in history:
    with st.chat_message(r): st.markdown(c)

st.divider()
with st.container():
    with st.expander("📎 Attach Media"):
        up_file = st.file_uploader("Upload", type=['png','jpg','jpeg','pdf','docx','txt'], key=f"f_{st.session_state.reset_key}")
    
    c_v, c_t = st.columns([1, 5])
    with c_v:
        v_text = speech_to_text(language='en', start_prompt="🎤", stop_prompt="🛑", key=f"v_{st.session_state.reset_key}")
    with c_t:
        u_text = st.chat_input("Ask Haris Neuro-Core...")

final_prompt = v_text if v_text else u_text

if final_prompt:
    with st.chat_message("user"): st.markdown(final_prompt)
    # Message save karte waqt email include kiya gaya hai
    manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "user", final_prompt, time.time()))

    with st.chat_message("assistant"):
        with st.spinner("Syncing..."):
            if up_file:
                if up_file.type.startswith("image/"):
                    res = st.session_state.neuro_engine.process_image(Image.open(up_file), final_prompt)
                else:
                    # Multi-format parsing
                    text = ""
                    if up_file.name.endswith('.pdf'):
                        pdf = PyPDF2.PdfReader(up_file); text = " ".join([p.extract_text() for p in pdf.pages])
                    elif up_file.name.endswith('.docx'):
                        doc = docx.Document(up_file); text = " ".join([p.text for p in doc.paragraphs])
                    res = st.session_state.neuro_engine.process_query(final_prompt, file_context=text)
            else:
                res = st.session_state.neuro_engine.process_query(final_prompt)
            st.markdown(res)
            manage_db("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (st.session_state.user_email, st.session_state.current_session, "assistant", res, time.time()))
    
    st.session_state.reset_key += 1
    st.rerun()

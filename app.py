import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image
from streamlit_mic_recorder import mic_recorder

# Page Config
st.set_page_config(page_title="HARIS NEURO-CORE", page_icon="🧠", layout="wide")

# Custom CSS for Branding
st.markdown("""
    <style>
    .main-title { font-size: 50px; font-weight: bold; color: #00FFAA; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- EMAIL LOGIN LOGIC ---
if "authenticated" not in st.session_state:
    st.markdown("<div class='main-title'>HARIS NEURO-CORE</div>", unsafe_allow_html=True)
    st.subheader("🔐 Secure Access Control")
    
    email = st.text_input("Email Address")
    user = st.text_input("Username")
    pas = st.text_input("Password", type="password")
    
    if st.button("Initialize Core"):
        if user == "haris" and pas == "neuro2026" and "@" in email:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.rerun()
        else:
            st.error("Access Denied: Invalid Credentials or Email")
    st.stop()

# Brain Setup
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- SIDEBAR (Lab & Voice) ---
with st.sidebar:
    st.title("🛡️ NEURO-LAB")
    st.write(f"Logged in as: `{st.session_state.user_email}`")
    st.divider()
    
    st.subheader("🎤 Voice Command")
    audio = mic_recorder(start_prompt="Click to Speak", stop_prompt="Stop Recording", key="voice_mic")
    
    st.divider()
    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], key="file_up")
    camera_photo = st.camera_input("Visual Sensor", key="neuro_cam")

# --- CHAT INTERFACE ---
st.markdown(f"<h1 style='text-align: center;'>🧠 HARIS NEURO-CORE</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process Input (Voice or Text)
user_input = st.chat_input("Ask HARIS NEURO-CORE...")
final_prompt = None

if audio:
    final_prompt = audio['text']
elif user_input:
    final_prompt = user_input

if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user"):
        st.markdown(final_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing Neural Pathways..."):
            image_to_process = None
            if camera_photo:
                image_to_process = Image.open(camera_photo)
            elif uploaded_file:
                image_to_process = Image.open(uploaded_file)

            if image_to_process:
                st.image(image_to_process, caption="Visual Data Received", width=300)
                response = st.session_state.neuro_engine.process_image(image_to_process, final_prompt)
            else:
                response = st.session_state.neuro_engine.process_query(final_prompt)
                
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

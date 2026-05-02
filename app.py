import streamlit as st
from engine import NeuroCoreEngine
from PIL import Image

# Page Config
st.set_page_config(page_title="NEURO-CORE AI", page_icon="🧠", layout="wide")

# Login logic
if "password_correct" not in st.session_state:
    st.title("🔐 NEURO-CORE Access")
    user = st.text_input("Username")
    pas = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "haris" and pas == "neuro2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# Brain Setup
groq_key = "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"
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- SIDEBAR FOR MULTIMEDIA ---
with st.sidebar:
    st.title("📂 NEURO-CORE Lab")
    st.info("Upload files or take a photo for analysis")
    
    uploaded_file = st.file_uploader("Upload Image/File", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'])
    camera_photo = st.camera_input("Take a Snapshot")

    if uploaded_file or camera_photo:
        st.success("File/Photo received!")
        # Yahan hum future mein Vision processing add karenge

# --- CHAT INTERFACE ---
# ... [Oopar ka sara purana login/sidebar code wese hi rahega] ...

# --- Sidebaer logic from previous step ---
st.sidebar.title("📂 NEURO-CORE Lab")
uploaded_file = st.sidebar.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
camera_photo = st.sidebar.camera_input("Take a Snapshot")

# --- CHAT INTERFACE ---
st.title("🧠 NEURO-CORE Cloud")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- PROCESSING ---
if prompt := st.chat_input("Ask about image or anything..."):
    # Pehle message display karen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            image_to_process = None
            if camera_photo:
                image_to_process = Image.open(camera_photo)
                st.image(image_to_process, caption="Analyzed Image", width=300)
            elif uploaded_file:
                image_to_process = Image.open(uploaded_file)
                st.image(image_to_process, caption="Analyzed File", width=300)

            # Vision aur Text ki smart switching
            if image_to_process:
                response = st.session_state.neuro_engine.process_image(image_to_process, prompt)
            else:
                response = st.session_state.neuro_engine.process_query(prompt)
                
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

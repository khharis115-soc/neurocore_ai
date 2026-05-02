import streamlit as st
from engine import NeuroCoreEngine

# Page Setup
st.set_page_config(page_title="NEURO-CORE AI", page_icon="🧠")

# 1. Secure Login
def check_password():
    def password_entered():
        if st.session_state["username"] == "haris" and st.session_state["password"] == "neuro2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 NEURO-CORE Access")
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# 2. API Key Security (Key yahan se uthayi jayegi)
# Streamlit Cloud par hum isay "Secrets" mein daalenge
groq_key = "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"

# Initialize Engine
if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# 3. Chat Interface
st.title("🧠 NEURO-CORE Cloud")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.neuro_engine.process_query(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

import streamlit as st
from engine import NeuroCoreEngine

# Page Config
st.set_page_config(page_title="NEURO-CORE AI", page_icon="🧠")

# Simple Login logic
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

# Chat Interface
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

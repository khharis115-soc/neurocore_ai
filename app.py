import os
import subprocess
import sys

# --- AUTO-INSTALLER LOGIC ---
# Ye code libraries ko khud install karega agar wo missing hon
def install_packages():
    required_packages = [
        "langchain", 
        "langchain-groq", 
        "langchain-community", 
        "duckduckgo-search", 
        "wikipedia", 
        "arxiv"
    ]
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Libraries install karein app shuru hone se pehle
install_packages()

import streamlit as st
from engine import NeuroCoreEngine

# --- PAGE CONFIG ---
st.set_page_config(page_title="NEURO-CORE AI", page_icon="🧠")

# --- LOGIN SYSTEM ---
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

# --- BRAIN SETUP (GROQ API) ---
# Yahan wahi API key hai jo aapne di thi
groq_key = "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"

if "neuro_engine" not in st.session_state:
    st.session_state.neuro_engine = NeuroCoreEngine(api_key=groq_key)

# --- CHAT INTERFACE ---
st.title("🧠 NEURO-CORE Cloud")
st.info("System Status: Online & Secure")

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
        with st.spinner("NEURO-CORE is thinking..."):
            response = st.session_state.neuro_engine.process_query(prompt)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

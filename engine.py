import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            self.text_llm = ChatGroq(
                temperature=0.6, 
                groq_api_key=api_key, 
                model_name="llama-3.3-70b-versatile"
            )
            self.search = DuckDuckGoSearchRun()
        except Exception as e:
            print(f"Engine Init Error: {e}")

    def process_query(self, user_input, file_context=None, history_context=""):
        try:
            # Internet search logic
            current_info = ""
            keywords = ["news", "today", "latest", "now", "weather", "aaj", "halat", "halat-e-hazra"]
            if any(word in user_input.lower() for word in keywords):
                try:
                    current_info = f"\n[LIVE INTERNET DATA]: {self.search.run(user_input)}"
                except:
                    current_info = "\n[LIVE INTERNET DATA]: Search unavailable, using base knowledge."

            # Hard Instructions
            system_instructions = (
                "You are HARIS NEURO-CORE, a powerful AI developed by Khawaja Haris Hassan. "
                "1. Answer EVERY query (Cybersecurity, Horoscope, General News, etc.). "
                "2. Mirror User Language (Roman Urdu for Roman Urdu). "
                "3. FILE ACCESS: If 'File Content' is provided below, use it to answer. Never say you can't see the file if content is present."
            )
            
            ctx_memory = f"\n[CHAT HISTORY]:\n{history_context}" if history_context else ""
            file_ctx = f"\n[FILE CONTENT/PDF]: {file_context}" if file_context else ""
            
            full_prompt = f"{system_instructions}{ctx_memory}{file_ctx}{current_info}\n\nUser: {user_input}"
            
            return self.text_llm.invoke(full_prompt).content
        except Exception as e:
            return f"Neural Error: {str(e)}"

    def process_image(self, image_data, prompt, history_context=""):
        try:
            buffered = BytesIO()
            image_data.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            completion = self.client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[
                    {"role": "system", "content": f"You are HARIS NEURO-CORE. Context: {history_context}"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt if prompt else "Analyze this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Vision Error: {str(e)}"

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
                temperature=0.4, 
                groq_api_key=api_key, 
                model_name="llama-3.3-70b-versatile"
            )
            self.search = DuckDuckGoSearchRun()
        except Exception as e:
            print(f"Engine Init Error: {e}")

    def process_query(self, user_input, file_context=None, history_context=""):
        try:
            # Current events ke liye search logic
            current_info = ""
            keywords = ["news", "today", "latest", "aaj", "halat", "weather", "score", "price"]
            if any(word in user_input.lower() for word in keywords):
                try:
                    current_info = f"\n[REAL-TIME DATA]: {self.search.run(user_input)}"
                except:
                    current_info = "\n[SEARCH]: Live search temporarily unavailable."

            system_instructions = (
                "You are HARIS NEURO-CORE, developed by Khawaja Haris Hassan. "
                "1. Use [FILE CONTENT] to answer if available. "
                "2. Use [REAL-TIME DATA] for current world events. "
                "3. Mirror the user's language: Respond in Roman Urdu if they use it, else English. "
                "4. Use Chat History to remember previous context."
            )
            
            file_ctx = f"\n[FILE CONTENT]: {file_context}" if file_context else ""
            ctx_memory = f"\n[CHAT HISTORY]:\n{history_context}" if history_context else ""
            
            full_prompt = f"{system_instructions}{file_ctx}{current_info}{ctx_memory}\n\nUser: {user_input}"
            return self.text_llm.invoke(full_prompt).content
        except Exception as e:
            return f"Neural Error: {str(e)}"

    def process_image(self, image_data, prompt):
        buffered = BytesIO()
        image_data.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        completion = self.client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}]}]
        )
        return completion.choices[0].message.content

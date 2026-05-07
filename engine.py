import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun # Internet search ke liye

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            self.text_llm = ChatGroq(
                temperature=0.5, 
                groq_api_key=api_key, 
                model_name="llama-3.3-70b-versatile"
            )
            self.search = DuckDuckGoSearchRun() # Search engine initialize
        except Exception as e:
            print(f"Engine Init Error: {e}")

    def process_query(self, user_input, file_context=None, history_context=""):
        try:
            # Step 1: Check if query needs latest info
            current_info = ""
            keywords = ["news", "today", "current", "latest", "now", "aaj", "halat", "weather"]
            if any(word in user_input.lower() for word in keywords):
                try:
                    current_info = f"\n[LATEST INTERNET DATA]: {self.search.run(user_input)}"
                except:
                    current_info = "\n[LATEST INTERNET DATA]: Search currently unavailable."

            # Step 2: System Instructions
            system_instructions = (
                "You are HARIS NEURO-CORE, an Omni-capable AI with Real-time Internet access. "
                "Developed by Khawaja Haris Hassan. "
                "Respond in professional English or Roman Urdu based on user input. "
                "Use the provided [LATEST INTERNET DATA] to answer questions about current events."
            )
            
            ctx_memory = f"\n[CHAT HISTORY]:\n{history_context}" if history_context else ""
            file_ctx = f"\n[FILE CONTENT]: {file_context}" if file_context else ""
            
            full_prompt = f"{system_instructions}{ctx_memory}{file_ctx}{current_info}\n\nUser Query: {user_input}"
            
            return self.text_llm.invoke(full_prompt).content
        except Exception as e:
            return f"Neural Error: {str(e)}"

    def process_image(self, image_data, prompt, history_context=""):
        # Image logic remains same
        try:
            buffered = BytesIO()
            image_data.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            completion = self.client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[
                    {"role": "system", "content": f"You are HARIS NEURO-CORE. Context: {history_context}"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt if prompt else "Analyze image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Vision Error: {str(e)}"

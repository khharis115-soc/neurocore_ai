import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            self.text_llm = ChatGroq(
                temperature=0.6, # Temperature thoda badhaya taake general topics par achi baat kare
                groq_api_key=api_key, 
                model_name="llama-3.3-70b-versatile"
            )
        except Exception as e:
            print(f"Engine Init Error: {e}")

    def process_query(self, user_input, file_context=None, history_context=""):
        try:
            # Ab ye prompt AI ko har cheez ka expert banaye ga
            system_instructions = (
                "You are HARIS NEURO-CORE, an Omni-capable AI Assistant developed by Khawaja Haris Hassan. "
                "PERSONALITY: Helpful, brilliant, and professional. "
                "KNOWLEDGE: You are an expert in Cyber Security, but you can also discuss ANY topic including "
                "horoscopes, general knowledge, creative writing, and daily tasks. NEVER say 'I am only a cyber AI'. "
                "MEMORY: Use 'Chat History' to stay in context. "
                "LANGUAGE: Mirror the user. Roman Urdu for Roman Urdu, English for English. No Hindi script."
            )
            
            ctx_memory = f"\n[CHAT HISTORY]:\n{history_context}" if history_context else ""
            file_ctx = f"\n[FILE CONTENT]: {file_context}" if file_context else ""
            
            full_prompt = f"{system_instructions}{ctx_memory}{file_ctx}\n\nUser: {user_input}"
            
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
                    {"role": "system", "content": f"You are HARIS NEURO-CORE. Context: {history_context}. You can analyze anything in this image."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt if prompt else "Analyze this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Vision Error: {str(e)}"

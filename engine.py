import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            # Llama 3.3 70B is the best for reasoning and memory
            self.text_llm = ChatGroq(
                temperature=0.4, 
                groq_api_key=api_key, 
                model_name="llama-3.3-70b-versatile"
            )
        except Exception as e:
            print(f"Engine Init Error: {e}")

    def process_query(self, user_input, file_context=None, history_context=""):
        try:
            # Memory and Language Instructions
            system_instructions = (
                "You are HARIS NEURO-CORE, a professional Cybersecurity AI. "
                "1. MEMORY: Use the 'Chat History' provided below to stay in context. "
                "2. LANGUAGE: If the user writes in Roman Urdu, respond in Roman Urdu. If in English, respond in English. "
                "3. NO HINDI: Strictly use Roman characters only. "
                "4. RELATE: If the user provides info (like a date), relate it to the previous conversation topics."
            )
            
            # Constructing the full prompt with history
            ctx_memory = f"\n[CHAT HISTORY]:\n{history_context}" if history_context else ""
            file_ctx = f"\n[FILE CONTENT]: {file_context}" if file_context else ""
            
            full_prompt = f"{system_instructions}{ctx_memory}{file_ctx}\n\nUser Query: {user_input}"
            
            return self.text_llm.invoke(full_prompt).content
        except Exception as e:
            return f"Neural Error: {str(e)}"

    def process_image(self, image_data, prompt, history_context=""):
        # Stable Vision Model
        model_id = "llama-3.2-90b-vision-preview"
        buffered = BytesIO()
        image_data.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        try:
            completion = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": f"You are HARIS NEURO-CORE. Context history: {history_context}"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt if prompt else "Analyze this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Vision Error: {str(e)}"

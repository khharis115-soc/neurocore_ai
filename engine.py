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
                temperature=0.2, # Kam temperature taake AI sirf file se jawab de
                groq_api_key=api_key, 
                model_name="llama-3.3-70b-versatile"
            )
        except Exception as e:
            print(f"Engine Init Error: {e}")

    def process_query(self, user_input, file_context=None, history_context=""):
        try:
            # Gemini-style Instructions
            system_instructions = (
                "You are HARIS NEURO-CORE. A file has been uploaded and its content is provided below. "
                "Your job is to act like a document assistant. Answer the user's questions based on the [FILE CONTENT]. "
                "If the answer is not in the file, use your general knowledge but mention it. "
                "Respond in the same language as the user (Roman Urdu/English)."
            )
            
            # Context build karna
            file_ctx = f"\n[FILE CONTENT]: {file_context}" if file_context else "\n[NO FILE UPLOADED]"
            history_ctx = f"\n[CHAT HISTORY]:\n{history_context}" if history_context else ""
            
            full_prompt = f"{system_instructions}{file_ctx}{history_ctx}\n\nUser Question: {user_input}"
            
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
                    {"role": "system", "content": "Analyze this image accurately."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt if prompt else "What is in this image?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Vision Error: {str(e)}"

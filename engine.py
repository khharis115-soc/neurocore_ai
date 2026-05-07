import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            # Latest stable model
            self.text_llm = ChatGroq(
                temperature=0.5, # Thoda temperature barhaya taake language natural lage
                groq_api_key=api_key, 
                model_name="llama-3.3-70b-versatile"
            )
        except Exception as e:
            print(f"Engine Init Error: {e}")

    def process_image(self, image_data, prompt):
        models = ["llama-3.2-90b-vision-preview", "llama-3.2-11b-vision-preview"]
        buffered = BytesIO()
        image_data.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        for model_id in models:
            try:
                completion = self.client.chat.completions.create(
                    model=model_id,
                    messages=[{
                        "role": "system", 
                        "content": "You are HARIS NEURO-CORE. IMPORTANT: Respond in the SAME LANGUAGE as the user's prompt (Roman Urdu or English). Do not use Hindi script."
                    },
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt if prompt else "Analyze this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}]
                )
                return completion.choices[0].message.content
            except Exception:
                continue 
        return "Vision Error: Models are currently updating."

    def process_query(self, user_input, file_context=None):
        try:
            # LANGUAGE DETECTION LOGIC IN SYSTEM PROMPT
            system_instructions = (
                "You are HARIS NEURO-CORE, a professional Cybersecurity AI Assistant. "
                "LANGUAGE RULE: If the user writes in Roman Urdu (e.g., 'kaise ho'), you MUST respond in Roman Urdu. "
                "If the user writes in English, you MUST respond in English. "
                "Keep the tone professional and expert. Do not use Hindi script or pure Urdu script."
            )
            
            ctx = f"Context from uploaded file: {file_context}\n\n" if file_context else ""
            full_prompt = f"{system_instructions}\n\n{ctx}User Query: {user_input}"
            
            return self.text_llm.invoke(full_prompt).content
        except Exception as e:
            return f"Neural Error: {str(e)}"

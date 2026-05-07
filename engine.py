import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            # Latest stable model for fast reasoning
            self.text_llm = ChatGroq(temperature=0.3, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
        except Exception as e:
            print(f"Init Error: {e}")

    def process_image(self, image_data, prompt):
        # Using currently active vision models on Groq
        models = ["llama-3.2-90b-vision-preview", "llama-3.2-11b-vision-preview"]
        
        buffered = BytesIO()
        image_data.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        for model_id in models:
            try:
                completion = self.client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt if prompt else "Explain this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}]
                )
                return completion.choices[0].message.content
            except Exception:
                continue 
        return "Vision Error: Models are currently busy or decommissioning. Please try again in a few minutes."

    def process_query(self, user_input, file_context=None):
        try:
            context_prefix = f"System: You are HARIS NEURO-CORE. Context from file: {file_context}\n\n" if file_context else "System: You are HARIS NEURO-CORE.\n\n"
            return self.text_llm.invoke(f"{context_prefix}User Question: {user_input}").content
        except Exception as e:
            if "401" in str(e):
                return "Neural Error: Your API Key is invalid or expired. Please check your dashboard."
            return f"Neural Error: {str(e)}"

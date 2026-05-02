import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        self.text_llm = ChatGroq(temperature=0.4, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")

    def process_image(self, image_data, prompt):
        try:
            buffered = BytesIO()
            image_data.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            completion = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": prompt if prompt else "Describe this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                ]}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Vision Error: {str(e)}"

    def process_query(self, user_input):
        try:
            return self.text_llm.invoke(f"System: You are HARIS NEURO-CORE. {user_input}").content
        except Exception as e:
            return f"Neural Error: {str(e)}"
            

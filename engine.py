import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        self.text_llm = ChatGroq(temperature=0.3, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")

    def process_image(self, image_data, prompt):
        models = ["llama-3.2-90b-vision-preview", "llama-3.2-11b-vision-preview"]
        buffered = BytesIO()
        image_data.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        for model_id in models:
            try:
                completion = self.client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": f"User Prompt: {prompt if prompt else 'Analyze this image in detail.'}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}]
                )
                return completion.choices[0].message.content
            except: continue
        return "Neural Vision Error: Vision models are currently busy. Please try again."

    def process_query(self, user_input, file_context=None):
        try:
            if file_context:
                full_prompt = f"Context from uploaded file: {file_context}\n\nUser Question: {user_input}"
            else:
                full_prompt = user_input
            
            return self.text_llm.invoke(f"System: You are HARIS NEURO-CORE, a professional AI. Answer the following: {full_prompt}").content
        except Exception as e:
            return f"Neural Error: {str(e)}"

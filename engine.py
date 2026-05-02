import base64
from io import BytesIO
from groq import Groq
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        self.text_llm = ChatGroq(temperature=0.3, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    def process_image(self, image_data, prompt):
        try:
            buffered = BytesIO()
            image_data.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Using the ONLY stable vision model name on Groq currently
            completion = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                ]}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Neural Vision Error: {str(e)}"

    def process_query(self, user_input):
        try:
            # Direct invoke for faster response without agent loops
            return self.text_llm.invoke(user_input).content
        except Exception as e:
            return f"Neural Error: {str(e)}"

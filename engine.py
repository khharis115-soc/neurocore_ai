import base64
from io import BytesIO
from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, AgentType
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.memory import ConversationBufferMemory
from groq import Groq

class NeuroCoreEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        self.text_llm = ChatGroq(
            temperature=0.3, 
            groq_api_key=api_key, 
            model_name="llama-3.3-70b-versatile"
        )
        self.search = DuckDuckGoSearchRun()
        self.wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        self.tools = [self.search, self.wiki]
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    def process_image(self, image_data, prompt):
        try:
            buffered = BytesIO()
            image_data.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # UPDATED MODEL NAME HERE: llama-3.2-90b-vision-preview
            completion = self.client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}]}],
                temperature=0.5
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Vision Error: {str(e)}"

    def process_query(self, user_input):
        try:
            agent = initialize_agent(
                self.tools, self.text_llm, 
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, 
                verbose=True, memory=self.memory, handle_parsing_errors=True
            )
            return agent.run(input=f"System: You are HARIS NEURO-CORE. {user_input}")
        except Exception as e:
            return f"Neural Error: {str(e)}"

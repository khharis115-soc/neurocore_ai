import os
from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, AgentType
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.memory import ConversationBufferMemory

class NeuroCoreEngine:
    def __init__(self, api_key):
        # Initialize Groq LLM
        self.llm = ChatGroq(
            temperature=0.3, 
            groq_api_key=api_key, 
            model_name="llama3-70b-8192"
        )
        
        # Tools setup (Sirf wahi jo requirements mein hain)
        self.search = DuckDuckGoSearchRun()
        self.wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        
        self.tools = [self.search, self.wiki]
        
        # Memory setup
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )

    def process_query(self, user_input):
        try:
            agent = initialize_agent(
                self.tools, 
                self.llm, 
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, 
                verbose=True, 
                memory=self.memory,
                handle_parsing_errors=True
            )
            response = agent.run(input=f"System: You are NEURO-CORE. Answer this: {user_input}")
            return response
        except Exception as e:
            return f"Error in Engine: {str(e)}"

from langchain_huggingface import HuggingFaceEndpoint
from langgraph.graph import StateGraph ,END ,START
from typing import TypedDict,Annotated
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import langchain_google_genai
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.graph import add_messages
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import sqlite3
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState) -> ChatState:
    messages = state.get("messages", [])
    response = model.invoke(messages)
    return {"messages": [response]}

load_dotenv()
llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",  
    task="text-generation",
    max_new_tokens=512,
    huggingfacehub_api_token=HF_API_KEY
) # type: ignore

model = ChatHuggingFace(llm=llm)

#if database not created it will 
from langgraph.checkpoint.memory import MemorySaver
try:
    conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)
except Exception as e:
    print("error",e)
#checkpointer
checkpointer = SqliteSaver(conn=conn)



graph = StateGraph(ChatState)
# add nodes
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)
parser = StrOutputParser()


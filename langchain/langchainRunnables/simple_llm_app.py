from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
import os
from langchain_core.prompts import PromptTemplate


llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",  
)

model = ChatHuggingFace(llm=llm)

prompt = PromptTemplate(
    template="suggest  catchy blog title about {topic}.",
    input_variables=['topic']
)


topic = input("enter a topic")

formatted_prompot = prompt.format(topic=topic)
print("fomatted prompt",formatted_prompot)
blog_title = llm.invoke(formatted_prompot)
print("blog Title : ",blog_title)
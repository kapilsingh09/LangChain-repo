from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",  # or another supported model
    task="text-generation",
    # huggingfacehub_api_token='use raw key if load env is not working'
)

model = ChatHuggingFace(llm=llm)

template1 = PromptTemplate(
    template="Write a detailed report on {topic}",
    input_variables=["topic"]
)

template2 = PromptTemplate(
    template="Write a 5-line summary of the following text:\n{report}",
    input_variables=["report"]
)

prompt1 = template1.invoke({"topic": "Black Hole"})
result = model.invoke(prompt1)
print(result.content)
print("-"*20)

prompt2 = template2.invoke({"report": result.content})
result1 = model.invoke(prompt2)

print(result1.content)
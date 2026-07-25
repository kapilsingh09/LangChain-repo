from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",  # or another supported model
    task="text-generation",
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

#parser
parser = StrOutputParser()

chain = template1 | model | parser |template2 | model | parser

result = chain.invoke({"topic":'black hole'})
print(result)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import pandas as pd
import io
import os

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0
)

template = PromptTemplate(
    template='generate 5 interesting fact about {topic}',
    input_variables=['topic']
)

parser = StrOutputParser()

chain = template | model | parser

result = chain.invoke({"topic":"cricket"})

print()
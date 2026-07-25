from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=1.2
)

parser = JsonOutputParser()

template = PromptTemplate(
    template="""
Give me 5 fact about {topic}.\n

{format_instructions}
""",
    input_variables=['topic'],
    partial_variables={
        "format_instructions": parser.get_format_instructions()
    },
)

chain = template | model | parser

result = chain.invoke({"topic":"black hole"})
print(result)
print(type(result))
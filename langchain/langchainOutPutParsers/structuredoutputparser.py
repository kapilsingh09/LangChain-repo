from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers.structured import (
    StructuredOutputParser,
    ResponseSchema,
)
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=1.2,
)

schema = [
    ResponseSchema(name="fact_1", description="Fact 1 about the topic"),
    ResponseSchema(name="fact_2", description="Fact 2 about the topic"),
    ResponseSchema(name="fact_3", description="Fact 3 about the topic"),
]

parser = StructuredOutputParser.from_response_schemas(schema)

template = PromptTemplate(
    template="""
Give 3 facts about {topic}.

{format_instruction}
""",
    input_variables=["topic"],
    partial_variables={
        "format_instruction": parser.get_format_instructions()
    },
)

prompt = template.invoke({"topic": "Black Hole"})

result = model.invoke(prompt)

print(parser.parse(result.content))
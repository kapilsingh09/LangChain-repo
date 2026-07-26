from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnableBranch
from pydantic import BaseModel, Field
from typing import Literal
import pandas as pd
import io
import os

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0
)



parser = StrOutputParser()


class Feedback(BaseModel):

    sentiment:Literal['positive','negative'] = Field(description='give the sentiment of the follwing feedback')


parser2 = PydanticOutputParser(pydantic_object=Feedback)
prompt1 = PromptTemplate(
    template="classify the sentiment of the following feedback text into positive or negative \n {feedback} \n {format_instruction}",
    input_variables=['feedback'],
    partial_variables={'format_instruction':parser2.get_format_instructions()}
)

classifier_chain = prompt1 | model | parser

print(classifier_chain.invoke({"text":"this is a terriable mobile phone"}))

branch_chain = RunnableBranch(
    (),
    (),
    ()
)
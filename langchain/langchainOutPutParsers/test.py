from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
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
    template="""
Generate details of 5 fictional Indian people.

Return ONLY CSV.

Columns:
name,age,city
"""
)

prompt = template.invoke({})

result = model.invoke(prompt)

# Gemini returns a list of content blocks
csv_text = result.content[0]["text"]

print(csv_text)

df = pd.read_csv(io.StringIO(csv_text))

print(df)

df.to_csv("people.csv", index=False)
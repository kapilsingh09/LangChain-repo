from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing_extensions import TypedDict
import os

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


class Review(TypedDict):
    summary: str
    sentiment: str


model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",   # Change if your account supports a different model
    temperature=0
)

structured_model = model.with_structured_output(Review)

result = structured_model.invoke("""
I recently upgraded to the Samsung Galaxy S24 Ultra, and I must say, it’s an absolute powerhouse! The Snapdragon 8 Gen 3 processor makes everything lightning fast—whether I’m gaming, multitasking, or editing photos. The 5000mAh battery easily lasts a full day even with heavy use, and the 45W fast charging is a lifesaver.

The S-Pen integration is a great touch for note-taking and quick sketches, though I don't use it often. What really blew me away is the 200MP camera—the night mode is stunning, capturing crisp, vibrant images even in low light.

However, the weight and size make it a bit uncomfortable for one-handed use. Also, Samsung’s One UI still comes with bloatware. The $1,300 price tag is also a hard pill to swallow.
""")

print(result['summary'])
print(result['sentiment'])
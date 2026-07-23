from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
hf_token = os.getenv("HF_TOKEN") or os.getenv("HF_API_KEY")

if not hf_token:
    raise RuntimeError("Set HF_TOKEN or HF_API_KEY in Chatmodels/.env")

llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",  
    task="text-generation",
    max_new_tokens=512,
    huggingfacehub_api_token=hf_token,
)

model = ChatHuggingFace(llm=llm)

result = model.invoke("what is the capital of india")
print(result.content)
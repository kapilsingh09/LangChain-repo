from fastapi import FastAPI
import time 
import uvicorn

app = FastAPI()

async def read_root():
    return {"message": "Welcome to the LangGraph RAG Chatbot API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/chat/{query}")
async def chat_with_bot(query: str):
    return {"response": f"You asked: {query}. This is a placeholder response from the LangGraph RAG Chatbot."}

if __name__ == "__main__":
    uvicorn.run(app,port=8000)
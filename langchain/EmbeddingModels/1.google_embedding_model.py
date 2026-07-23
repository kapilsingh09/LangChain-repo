import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",  # or "text-embedding-004"
    output_dimensionality=32 # Optional: reduces vector size if needed (e.g. 768, 1536)
)


# google_api_key=api_key
# 2. Embed a single query (returns a List[float])
query_text = "What is the capital of India?"
query_vector = embeddings.embed_query(query_text)

# print(f"Query Vector Length: {len(query_vector)}")
# print(f"Sample values: {query_vector[:6]}")

# 3. Embed a list of documents for indexing
documents = [
    "New Delhi is the capital of India.",
    "Paris is the capital of France.",
    "Tokyo is the capital of Japan."
]
doc_vectors = embeddings.embed_documents(documents)
print(doc_vectors)
# print(f"Generated {len(doc_vectors)} document embeddings.")
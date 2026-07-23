import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
# import numpy as np
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")



embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    output_dimensionality=32
) 

query_text = "What is the capital of India?"
query_vector = embeddings.embed_query(query_text)

print(f"Query Vector Length: {len(query_vector)}")
print(f"Sample values: {query_vector[:6]}")

documents = [
    "Cricket is a bat-and-ball sport played between two teams of eleven players.",
    "A cricket match is played on an oval-shaped field with a 22-yard pitch in the center.",
    "Virat Kohli is one of India's greatest batsmen and has scored many international centuries.",
    "Rohit Sharma is famous for his elegant batting and multiple double centuries in One Day Internationals.",
    "Jasprit Bumrah is known for his unique bowling action and deadly yorkers.",
    "Sachin Tendulkar is called the God of Cricket and scored 100 international centuries.",
    "The ICC Cricket World Cup is held every four years and features the best cricket-playing nations.",
    "A batsman scores runs by hitting the ball and running between the wickets or by hitting boundaries.",
    "A bowler aims to dismiss the batsman by taking wickets while conceding as few runs as possible.",
    "The Indian Premier League (IPL) is one of the most popular T20 cricket leagues in the world."
]

document_vertors = embeddings.embed_documents(documents)
query = "Who is known as the God of Cricket?"

query_vector = embeddings.embed_query(query)

similarities = cosine_similarity([query_vector], document_vertors)[0]

for doc, score in zip(documents, similarities):
    print(f"{score:.4f} -> {doc}")

best_index = similarities.argmax()

print("\nMost Relevant Document:")
print(documents[best_index])
print(f"Similarity Score: {similarities[best_index]:.4f}")
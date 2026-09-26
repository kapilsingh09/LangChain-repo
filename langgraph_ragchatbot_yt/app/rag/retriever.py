from .vector_store import create_vector_store   

from ingestion.transcript import chunks
from .embedding import embedding_model

retriever = create_vector_store(chunks, embedding_model).as_retriever(search_kwargs={"k": 3})

if __name__ == "__main__":
    query = "What is discussed about neural networks?"

    results = retriever.invoke(query, k=3)

    for doc in results:
        print(doc.page_content)
        print(doc.metadata)
        print("---")
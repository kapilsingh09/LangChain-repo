import sys
from pathlib import Path
from langchain_community.vectorstores import FAISS

# Correct Syntax using from_documents
def create_vector_store(chunks, embedding_model):
    return FAISS.from_documents(
        documents=chunks,
        embedding=embedding_model,
    )

# if __name__ == "__main__":
#     print("Number of chunks:", len(chunks))
#     vector_store = create_vector_store(chunks, embedding_model)
#     print("Number of vectors in the vector store:", len(vector_store.index_to_docstore_id))
#     print("Vector store created successfully.")
#     print(len(vector_store.index_to_docstore_id))
#     print("working")

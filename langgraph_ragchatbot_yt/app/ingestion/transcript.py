from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from .youtube import YT_WATCH_ID, transcipt
except ImportError:
    from youtube import YT_WATCH_ID, transcipt


# 1. Combine transcript snippets into one continuous text
full_text = " ".join(
    snippet.text for snippet in transcipt.snippets
)


# 2. Create a mapping from character position → tiṇmestamp
char_timestamps = []

current_position = 0

for snippet in transcipt.snippets:
    text = snippet.text
    start = snippet.start

    char_timestamps.append({
        "start_char": current_position,
        "end_char": current_position + len(text),
        "start_seconds": start
    })

    current_position += len(text) + 1  # +1 for the space


# 3. Split the continuous transcript
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)

text_chunks = splitter.create_documents([full_text])


# 4. Attach timestamp metadata to every chunk
chunks = []

for chunk in text_chunks:
    chunk_start = full_text.find(chunk.page_content)

    # Find transcript snippet containing the beginning of this chunk
    timestamp = 0.0

    for item in char_timestamps:
        if item["start_char"] <= chunk_start < item["end_char"]:
            timestamp = item["start_seconds"]
            break

    chunks.append(
        Document(
            page_content=chunk.page_content,
            metadata={
                "start": timestamp,
                "source": YT_WATCH_ID
            }
        )
    )


# print("Number of chunks:", len(chunks))

# for i, chunk in enumerate(chunks[:3]):
#     print(f"\n--- CHUNK {i} ---")
#     print(chunk.page_content)
#     print("Length:", len(chunk.page_content))
#     print("Metadata:", chunk.metadata)
# print("Transcript ingestion and chunking completed successfully.")
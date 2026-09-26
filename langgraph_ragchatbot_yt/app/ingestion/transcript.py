from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ingestion.youtube import fetch_transcript


def build_chunks(video_id: str) -> list[Document]:
    """
    Fetch the YouTube transcript for `video_id`, split it into chunks,
    and return a list of LangChain Documents with timestamp metadata.
    """
    transcript = fetch_transcript(video_id)

    # 1. Combine transcript snippets into one continuous text
    full_text = " ".join(snippet.text for snippet in transcript.snippets)

    # 2. Create a mapping from character position → timestamp
    char_timestamps = []
    current_position = 0

    for snippet in transcript.snippets:
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
                    "source": video_id
                }
            )
        )

    return chunks
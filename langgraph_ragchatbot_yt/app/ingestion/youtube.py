from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled


def fetch_transcript(video_id: str):
    """
    Fetch the YouTube transcript for a given video ID.
    Returns the transcript object or raises an exception.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        return transcript
    except TranscriptsDisabled as e:
        raise RuntimeError(f"Transcripts are disabled for video '{video_id}': {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript for video '{video_id}': {e}")
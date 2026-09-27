from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled


def fetch_transcript(video_id: str):
    """
    Fetch an English or Hindi transcript when available, otherwise use the
    video's first available transcript language.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcripts = ytt_api.list(video_id)
        available_transcripts = list(transcripts)

        english_transcript = next(
            (
                item for item in available_transcripts
                if item.language_code.lower().startswith("en")
                and not item.is_generated
            ),
            None,
        ) or next(
            (
                item for item in available_transcripts
                if item.language_code.lower().startswith("en")
            ),
            None,
        )
        hindi_transcript = next(
            (
                item for item in available_transcripts
                if item.language_code.lower().startswith("hi")
            ),
            None,
        )
        transcript = (
            english_transcript
            or hindi_transcript
            or next(iter(available_transcripts), None)
        )

        if transcript is None:
            raise RuntimeError(f"No transcript tracks are available for video '{video_id}'.")

        print(
            f"[Transcript] Using {transcript.language_code} transcript "
            f"(generated={transcript.is_generated}) for {video_id}"
        )
        return transcript.fetch()
    except TranscriptsDisabled as e:
        raise RuntimeError(f"Transcripts are disabled for video '{video_id}': {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript for video '{video_id}': {e}")
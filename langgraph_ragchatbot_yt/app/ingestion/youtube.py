from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled


def fetch_transcript(video_id: str):
    """
    Priority:
    1. English manual transcript
    2. English generated transcript
    3. Hindi transcript
    4. Any other available transcript
    """

    try:
        ytt_api = YouTubeTranscriptApi()
        transcripts = list(ytt_api.list(video_id))

        if not transcripts:
            raise RuntimeError(
                f"No transcript tracks are available for video '{video_id}'."
            )

        # 1. English manual transcript
        transcript = next(
            (
                t for t in transcripts
                if t.language_code.lower().startswith("en")
                and not t.is_generated
            ),
            None
        )

        # 2. English generated transcript
        if transcript is None:
            transcript = next(
                (
                    t for t in transcripts
                    if t.language_code.lower().startswith("en")
                ),
                None
            )

        # 3. Hindi transcript
        if transcript is None:
            transcript = next(
                (
                    t for t in transcripts
                    if t.language_code.lower().startswith("hi")
                ),
                None
            )

        # 4. Any other available language
        if transcript is None:
            transcript = transcripts[0]

        print(
            f"[Transcript] Using {transcript.language_code} "
            f"(generated={transcript.is_generated}) for {video_id}"
        )

        return transcript.fetch()

    except TranscriptsDisabled as e:
        raise RuntimeError(
            "Transcripts are disabled for this video, so I can't access its transcript. "
            "Please try another YouTube video with captions enabled."
        ) from e

    except Exception as e:
        raise RuntimeError(
            f"Failed to fetch transcript for video '{video_id}': {e}"
        )


# code behaviour 

# Available transcripts
#         │
#         ├── English manual? ──→ YES → USE IT
#         │
#         ├── English generated? → YES → USE IT
#         │
#         ├── Hindi? ────────────→ YES → USE IT
#         │
#         └── Anything else? ───→ YES → USE IT
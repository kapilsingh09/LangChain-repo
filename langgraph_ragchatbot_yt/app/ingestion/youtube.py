from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
YT_WATCH_ID = "OYvlznJ4IZQ"

try:
  ytt_api = YouTubeTranscriptApi()
  
  transcipt = ytt_api.fetch(YT_WATCH_ID)

except TranscriptsDisabled as e:
  print(e,"Transcripts are disabled for this video.")
except Exception as e:
  print(e,"An error occurred while fetching the YouTube transcript.")
  
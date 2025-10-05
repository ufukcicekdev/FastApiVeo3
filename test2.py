import time
from google import genai
from google.genai import types

client = genai.Client()

operation = client.models.generate_videos(
    model="veo-3.0-fast-generate-001",
    prompt="a close-up shot of a golden retriever playing in a field of sunflowers",
    config=types.GenerateVideosConfig(
      negative_prompt="barking, woofing",
      aspect_ratio="9:16",
      resolution="720p",
    ),
)

# Waiting for the video(s) to be generated
while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)
    print(operation)

generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("golden_retriever.mp4")
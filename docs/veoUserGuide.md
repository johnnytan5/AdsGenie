Generate videos with Veo 3.1 in Gemini API

content_copy

Veo 3.1 is Google's state-of-the-art model for generating high-fidelity, 8-second 720p or 1080p videos featuring stunning realism and natively generated audio. You can access this model programmatically using the Gemini API. To learn more about the available Veo model variants, see the Model Versions section.

Veo 3.1 excels at a wide range of visual and cinematic styles and introduces several new capabilities:

Video extension: Extend videos that were previously generated using Veo.
Frame-specific generation: Generate a video by specifying the first and last frames.
Image-based direction: Use up to three reference images to guide the content of your generated video.
For more information about writing effective text prompts for video generation, see the Veo prompt guide

Text to video generation

Choose an example to see how to generate a video with dialogue, cinematic realism, or creative animation:

Dialogue & Sound Effects  Cinematic Realism  Creative Animation

Python
JavaScript
Go
REST

import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """A close up of two people staring at a cryptic drawing on a wall, torchlight flickering.
A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'"""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video.
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("dialogue_example.mp4")
print("Generated video saved to dialogue_example.mp4")


Image to video generation

The following code demonstrates generating an image using Gemini 2.5 Flash Image aka Nano Banana, then using that image as the starting frame for generating a video with Veo 3.1.

Python
JavaScript
Go

import time
from google import genai

client = genai.Client()

prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"

# Step 1: Generate an image with Nano Banana.
image = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
    config={"response_modalities":['IMAGE']}
)

# Step 2: Generate video with Veo 3.1 using the image.
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    image=image.parts[0].as_image(),
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video.
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3_with_image_input.mp4")
print("Generated video saved to veo3_with_image_input.mp4")
Using reference images

Note: This feature is available for Veo 3.1 models only
Veo 3.1 now accepts up to 3 reference images to guide your generated video's content. Provide images of a person, character, or product to preserve the subject's appearance in the output video.

For example, using these three images generated with Nano Banana as references with a well-written prompt creates the following video:

`dress_image`	`woman_image`	`glasses_image`
High-fashion flamingo dress with layers of pink and fuchsia feathers	Beautiful woman with dark hair and warm brown eyes	Whimsical pink, heart-shaped sunglasses
Python

import time
from google import genai

client = genai.Client()

prompt = "The video opens with a medium, eye-level shot of a beautiful woman with dark hair and warm brown eyes. She wears a magnificent, high-fashion flamingo dress with layers of pink and fuchsia feathers, complemented by whimsical pink, heart-shaped sunglasses. She walks with serene confidence through the crystal-clear, shallow turquoise water of a sun-drenched lagoon. The camera slowly pulls back to a medium-wide shot, revealing the breathtaking scene as the dress's long train glides and floats gracefully on the water's surface behind her. The cinematic, dreamlike atmosphere is enhanced by the vibrant colors of the dress against the serene, minimalist landscape, capturing a moment of pure elegance and high-fashion fantasy."

dress_reference = types.VideoGenerationReferenceImage(
  image=dress_image, # Generated separately with Nano Banana
  reference_type="asset"
)

sunglasses_reference = types.VideoGenerationReferenceImage(
  image=glasses_image, # Generated separately with Nano Banana
  reference_type="asset"
)

woman_reference = types.VideoGenerationReferenceImage(
  image=woman_image, # Generated separately with Nano Banana
  reference_type="asset"
)

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=types.GenerateVideosConfig(
      reference_images=[dress_reference, glasses_reference, woman_reference],
    ),
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video.
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_with_reference_images.mp4")
print("Generated video saved to veo3.1_with_reference_images.mp4")


Using first and last frames

Note: This feature is available for Veo 3.1 models only
Veo 3.1 lets you create videos using interpolation, or specifying the first and last frames of the video. For information about writing effective text prompts for video generation, see the Veo prompt guide.

Python

import time
from google import genai

client = genai.Client()

prompt = "A cinematic, haunting video. A ghostly woman with long white hair and a flowing dress swings gently on a rope swing beneath a massive, gnarled tree in a foggy, moonlit clearing. The fog thickens and swirls around her, and she slowly fades away, vanishing completely. The empty swing is left swaying rhythmically on its own in the eerie silence."

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    image=first_image, # Generated separately with Nano Banana
    config=types.GenerateVideosConfig(
      last_frame=last_image # Generated separately with Nano Banana
    ),
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video.
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_with_interpolation.mp4")
print("Generated video saved to veo3.1_with_interpolation.mp4")
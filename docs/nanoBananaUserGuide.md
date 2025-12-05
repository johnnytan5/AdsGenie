Image generation with Gemini (aka Nano Banana & Nano Banana Pro)

content_copy

Gemini can generate and process images conversationally. You can prompt either the fast Gemini 2.5 Flash (aka Nano Banana) or the advanced Gemini 3 Pro Preview (aka Nano Banana Pro) image models with text, images, or a combination of both, allowing you to create, edit, and iterate on visuals with unprecedented control:

Text, Image, and Multi-Image to Image: Generate high-quality images from text descriptions, use text prompts to edit and adjust a given image, or use multiple input images to compose new scenes and transfer styles.
Iterative refinement: Conversationally refine your image over multiple turns, making small adjustments until it's perfect.
High-Fidelity text rendering: Accurately generate images that contain legible and well-placed text, ideal for logos, diagrams, and posters.
All generated images include a SynthID watermark.

Image generation (text-to-image)

Python
JavaScript
Go
Java
REST

from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = (
    "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
AI-generated image of a nano banana dish
AI-generated image of a nano banana dish in a Gemini-themed restaurant
Image editing (text-and-image-to-image)

Reminder: Make sure you have the necessary rights to any images you upload. Don't generate content that infringe on others' rights, including videos or images that deceive, harass, or harm. Your use of this generative AI service is subject to our Prohibited Use Policy.

Provide an image and use text prompts to add, remove, or modify elements, change the style, or adjust the color grading.

The following example demonstrates uploading base64 encoded images. For multiple images, larger payloads, and supported MIME types, check the Image understanding page.

Python
JavaScript
Go
Java
REST

from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = (
    "Create a picture of my cat eating a nano-banana in a "
    "fancy restaurant under the Gemini constellation",
)

image = Image.open("/path/to/cat_image.png")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt, image],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
AI-generated image of a cat eating anano banana
AI-generated image of a cat eating a nano banana
Multi-turn image editing

Keep generating and editing images conversationally. Chat or multi-turn conversation is the recommended way to iterate on images. The following example shows a prompt to generate an infographic about photosynthesis.

Python
Javascript
Go
Java
REST

from google import genai
from google.genai import types

client = genai.Client()

chat = client.chats.create(
    model="gemini-3-pro-image-preview",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        tools=[{"google_search": {}}]
    )
)

message = "Create a vibrant infographic that explains photosynthesis as if it were a recipe for a plant's favorite food. Show the \"ingredients\" (sunlight, water, CO2) and the \"finished dish\" (sugar/energy). The style should be like a page from a colorful kids' cookbook, suitable for a 4th grader."

response = chat.send_message(message)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif image:= part.as_image():
        image.save("photosynthesis.png")
AI-generated infographic about photosynthesis
AI-generated infographic about photosynthesis
You can then use the same chat to change the language on the graphic to Spanish.

Python
Javascript
Go
Java
REST

message = "Update this infographic to be in Spanish. Do not change any other elements of the image."
aspect_ratio = "16:9" # "1:1","2:3","3:2","3:4","4:3","4:5","5:4","9:16","16:9","21:9"
resolution = "2K" # "1K", "2K", "4K"

response = chat.send_message(message,
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=resolution
        ),
    ))

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif image:= part.as_image():
        image.save("photosynthesis_spanish.png")
AI-generated infographic of photosynthesis in Spanish
AI-generated infographic of photosynthesis in Spanish
New with Gemini 3 Pro Image

Gemini 3 Pro Image (gemini-3-pro-image-preview) is a state-of-the-art image generation and editing model optimized for professional asset production. Designed to tackle the most challenging workflows through advanced reasoning, it excels at complex, multi-turn creation and modification tasks.

High-resolution output: Built-in generation capabilities for 1K, 2K, and 4K visuals.
Advanced text rendering: Capable of generating legible, stylized text for infographics, menus, diagrams, and marketing assets.
Grounding with Google Search: The model can use Google Search as a tool to verify facts and generate imagery based on real-time data (e.g., current weather maps, stock charts, recent events).
Thinking mode: The model utilizes a "thinking" process to reason through complex prompts. It generates interim "thought images" (visible in the backend but not charged) to refine the composition before producing the final high-quality output.
Up to 14 reference images: You can now mix up to 14 reference images to produce the final image.
Use up to 14 reference images

Gemini 3 Pro Preview lets you to mix up to 14 reference images. These 14 images can include the following:

Up to 6 images of objects with high-fidelity to include in the final image
Up to 5 images of humans to maintain character consistency
Python
Javascript
Go
Java
REST

from google import genai
from google.genai import types
from PIL import Image

prompt = "An office group photo of these people, they are making funny faces."
aspect_ratio = "5:4" # "1:1","2:3","3:2","3:4","4:3","4:5","5:4","9:16","16:9","21:9"
resolution = "2K" # "1K", "2K", "4K"

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        prompt,
        Image.open('person1.png'),
        Image.open('person2.png'),
        Image.open('person3.png'),
        Image.open('person4.png'),
        Image.open('person5.png'),
    ],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=resolution
        ),
    )
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif image:= part.as_image():
        image.save("office.png")
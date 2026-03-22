import os
from PIL import Image, ImageDraw

def create_image(text, filename):
    img = Image.new('RGB', (400, 400), color=(30, 30, 50))
    d = ImageDraw.Draw(img)
    # Simple text (default font)
    d.text((50, 180), text, fill=(255, 255, 255))
    img.save(filename)

os.makedirs("test_input", exist_ok=True)

categories = {
    "mountains": 6,
    "receipts": 6,
    "dogs": 6,
    "cars": 6
}

for cat, count in categories.items():
    for i in range(count):
        create_image(f"A high quality photo of {cat} {i}", f"test_input/{cat}_{i}.jpg")

print("Test images created in test_input/")

import json
import mimetypes
from pathlib import Path

from django.conf import settings
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def analyze_receipt(image_path: str) -> dict:
    path = Path(image_path)

    with open(path, 'rb') as f:
        image_bytes = f.read()

    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = 'image/jpeg'

    prompt = """
    Проанализируй изображение кассового чека и верни JSON с полями:
    cafe_name
    receipt_date
    receipt_time
    total_amount
    currency
    items:
      - name
      - quantity
      - unit_price
      - line_total
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ],
    )

    if not response.text:
        raise ValueError('Gemini не вернул text-ответ')

    return json.loads(response.text)

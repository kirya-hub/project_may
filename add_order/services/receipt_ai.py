import io
import json
import mimetypes
from pathlib import Path

from django.conf import settings
from google import genai
from google.genai import types
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def preprocess_image(image_path: str) -> bytes:
    img = Image.open(image_path)

    img = ImageOps.exif_transpose(img)

    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.filter(ImageFilter.MedianFilter(size=3))

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    return buffer.getvalue()


def analyze_receipt(image_path: str) -> dict:
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f'Файл чека не найден: {image_path}')

    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = 'image/jpeg'

    image_bytes = preprocess_image(image_path)

    schema = {
        'type': 'object',
        'properties': {
            'cafe_name': {'type': ['string', 'null']},
            'receipt_date': {'type': ['string', 'null']},
            'receipt_time': {'type': ['string', 'null']},
            'receipt_number': {'type': ['string', 'null']},
            'fiscal_number': {'type': ['string', 'null']},
            'total_amount': {'type': ['number', 'null']},
            'currency': {'type': ['string', 'null']},
            'items': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'quantity': {'type': ['number', 'null']},
                        'unit_price': {'type': ['number', 'null']},
                        'line_total': {'type': ['number', 'null']},
                    },
                    'required': ['name'],
                },
            },
            'raw_text_summary': {'type': ['string', 'null']},
        },
        'required': ['items'],
    }

    prompt = """
Проанализируй изображение кассового чека и верни JSON.
Если на чеке есть номер чека или фискальный номер — тоже верни их в соответствующие поля.
Для даты и времени постарайся вернуть ровно то, что видно на чеке.
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), prompt],
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_json_schema=schema,
        ),
    )

    raw_text = (response.text or '').strip()
    if not raw_text:
        raise ValueError('Gemini вернул пустой ответ')

    return json.loads(raw_text)

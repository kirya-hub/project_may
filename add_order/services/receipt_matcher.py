import re
from difflib import SequenceMatcher

from cafes.models import Cafe, MenuItem


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace('"', '')
    text = text.replace('«', '').replace('»', '')
    text = text.replace('ё', 'е')
    text = re.sub(r'\b\d+[\/\d]*\b', ' ', text)
    text = re.sub(r'\b\d+[.,]?\d*\s*(л|мл|г|кг)\b', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def match_cafe(parsed_cafe_name: str) -> 'Cafe | None':
    normalized = normalize(parsed_cafe_name)
    best_cafe = None
    best_score = 0.0

    for cafe in Cafe.objects.only('id', 'name'):
        score = similarity(normalized, normalize(cafe.name))
        if score > best_score:
            best_score = score
            best_cafe = cafe

    if best_score >= 0.6:
        return best_cafe
    return None


def match_items(receipt_items, cafe):
    menu_items = list(MenuItem.objects.filter(category__cafe=cafe).only('id', 'name'))

    result = []
    matched_total = 0.0

    for item in receipt_items:
        receipt_name = item.get('name', '')
        normalized_receipt_name = normalize(receipt_name)

        best_item = None
        best_score = 0.0

        for menu_item in menu_items:
            score = similarity(normalized_receipt_name, normalize(menu_item.name))
            if score > best_score:
                best_score = score
                best_item = menu_item

        matched = best_score >= 0.7

        line_total = item.get('line_total') or 0.0
        if matched and best_item:
            matched_total += line_total

        result.append(
            {
                'receipt_name': receipt_name,
                'menu_item': best_item.name if best_item else None,
                'score': round(best_score, 3),
                'matched': matched,
                'line_total': line_total,
            }
        )

    return result, matched_total

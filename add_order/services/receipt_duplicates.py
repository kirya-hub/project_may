from __future__ import annotations

import hashlib
import io
import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db.models import Q
from PIL import Image, ImageOps

from add_order.models import Order

logger = logging.getLogger(__name__)

DHASH_SIZE = 8
AHASH_SIZE = 8
DHASH_MAX_DISTANCE = 10
AHASH_MAX_DISTANCE = 10
TOKEN_SIMILARITY_THRESHOLD = 0.72


def _open_normalized_image(image_path: str) -> Image.Image:
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ('L', 'RGB'):
        img = img.convert('RGB')
    return img


def _pixel_to_int(value: Any) -> int:
    if isinstance(value, tuple):
        if not value:
            return 0
        first = value[0]
        return int(first) if first is not None else 0
    if value is None:
        return 0
    return int(value)


def _clean_text(value: Any) -> str:
    return ' '.join(str(value or '').strip().lower().split())


def _digits_only(value: Any) -> str:
    return ''.join(ch for ch in str(value or '') if ch.isdigit())


def _normalized_decimal(value: Any) -> str:
    if value in (None, '', 'null'):
        return ''
    try:
        return format(Decimal(str(value)).quantize(Decimal('0.01')), 'f')
    except (InvalidOperation, ValueError):
        return str(value).strip()


def _decimal_or_none(value: Any) -> Decimal | None:
    if value in (None, '', 'null'):
        return None
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _only_letters_digits_spaces(value: str) -> str:
    value = value.lower()
    value = re.sub(r'[^a-zа-я0-9\s]+', ' ', value, flags=re.IGNORECASE)
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def _normalized_text_block(value: Any) -> str:
    return _only_letters_digits_spaces(str(value or ''))


def _normalized_date_key(value: Any) -> str:
    digits = _digits_only(value)
    if len(digits) >= 8:
        return digits[:8]
    return digits


def _item_names_from_data(data: dict[str, Any] | None) -> str:
    if not isinstance(data, dict):
        return ''
    items = data.get('items') or []
    names: list[str] = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                name = _clean_text(item.get('name'))
                if name:
                    names.append(name)
    return ' | '.join(names)


def _raw_summary_from_data(data: dict[str, Any] | None) -> str:
    if not isinstance(data, dict):
        return ''
    return _clean_text(data.get('raw_text_summary'))


def _build_receipt_text_fingerprint_from_data(data: dict[str, Any] | None) -> str:
    if not isinstance(data, dict):
        return ''

    parts = [
        _normalized_text_block(data.get('cafe_name')),
        _normalized_text_block(data.get('receipt_date')),
        _normalized_text_block(data.get('receipt_time')),
        _normalized_text_block(data.get('receipt_number')),
        _normalized_text_block(data.get('fiscal_number')),
        _normalized_decimal(data.get('total_amount')),
        _normalized_text_block(data.get('raw_text_summary')),
        _normalized_text_block(_item_names_from_data(data)),
    ]

    parts = [p for p in parts if p]
    return ' || '.join(parts)


STOP_WORDS = {
    'ооо',
    'руб',
    'рублей',
    'ruble',
    'rubles',
    'итого',
    'сумма',
    'всего',
    'чек',
    'касса',
    'стол',
    'гостей',
    'заказ',
    'закрыт',
    'открыт',
    'наличными',
    'карта',
    'картой',
    'оплачено',
}


def _fingerprint_tokens(data: dict[str, Any] | None) -> set[str]:
    fp = _build_receipt_text_fingerprint_from_data(data)
    if not fp:
        return set()

    tokens = set()
    for token in _only_letters_digits_spaces(fp).split():
        if len(token) < 3:
            continue
        if token in STOP_WORDS:
            continue
        tokens.add(token)
    return tokens


def _token_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def file_sha256(image_path: str, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(image_path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_image_bytes(image_path: str) -> bytes:
    img = _open_normalized_image(image_path)
    img = img.convert('L')
    img.thumbnail((1200, 1200))

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def _auto_receipt_crop(img: Image.Image) -> Image.Image:
    gray = img.convert('L')
    width, height = gray.size
    if width < 80 or height < 80:
        return img

    threshold = 185
    step_x = max(1, width // 300)
    step_y = max(1, height // 300)

    min_x, min_y = width, height
    max_x, max_y = 0, 0
    found = False

    for y in range(0, height, step_y):
        for x in range(0, width, step_x):
            if _pixel_to_int(gray.getpixel((x, y))) >= threshold:
                found = True
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y

    if not found:
        return img

    if (max_x - min_x) < width * 0.25 or (max_y - min_y) < height * 0.25:
        return img

    pad_x = int(width * 0.03)
    pad_y = int(height * 0.03)
    left = max(0, min_x - pad_x)
    top = max(0, min_y - pad_y)
    right = min(width, max_x + pad_x)
    bottom = min(height, max_y + pad_y)

    if right <= left or bottom <= top:
        return img

    return img.crop((left, top, right, bottom))


def _dhash_from_image(img: Image.Image, size: int = DHASH_SIZE) -> str:
    gray = img.convert('L').resize((size + 1, size), Image.Resampling.LANCZOS)

    bits: list[str] = []
    for y in range(size):
        for x in range(size):
            left = _pixel_to_int(gray.getpixel((x, y)))
            right = _pixel_to_int(gray.getpixel((x + 1, y)))
            bits.append('1' if left > right else '0')

    return f'{int("".join(bits), 2):0{size * size // 4}x}'


def _ahash_from_image(img: Image.Image, size: int = AHASH_SIZE) -> str:
    gray = img.convert('L').resize((size, size), Image.Resampling.LANCZOS)

    pixels: list[int] = []
    for y in range(size):
        for x in range(size):
            pixels.append(_pixel_to_int(gray.getpixel((x, y))))

    avg = sum(pixels) / max(1, len(pixels))
    bits = ['1' if px >= avg else '0' for px in pixels]
    return f'{int("".join(bits), 2):0{size * size // 4}x}'


def image_dhash(image_path: str, size: int = DHASH_SIZE) -> str:
    img = _open_normalized_image(image_path)
    return _dhash_from_image(img, size=size)


def _center_crop(img: Image.Image, margin_ratio: float) -> Image.Image:
    width, height = img.size
    if width < 20 or height < 20:
        return img

    dx = int(width * margin_ratio)
    dy = int(height * margin_ratio)

    left = max(0, dx)
    top = max(0, dy)
    right = min(width, width - dx)
    bottom = min(height, height - dy)

    if right <= left or bottom <= top:
        return img

    return img.crop((left, top, right, bottom))


def image_hash_variants(image_path: str) -> list[tuple[str, str]]:
    img = _open_normalized_image(image_path)
    receipt_crop = _auto_receipt_crop(img)

    variants = [
        ('d', _dhash_from_image(img)),
        ('d', _dhash_from_image(_center_crop(img, 0.08))),
        ('d', _dhash_from_image(receipt_crop)),
        ('d', _dhash_from_image(_center_crop(receipt_crop, 0.08))),
        ('a', _ahash_from_image(img)),
        ('a', _ahash_from_image(_center_crop(img, 0.08))),
        ('a', _ahash_from_image(receipt_crop)),
        ('a', _ahash_from_image(_center_crop(receipt_crop, 0.08))),
    ]

    unique_variants: list[tuple[str, str]] = []
    for value in variants:
        if value[1] and value not in unique_variants:
            unique_variants.append(value)
    return unique_variants


def hamming_distance(hex_a: str, hex_b: str) -> int:
    if not hex_a or not hex_b:
        return 999
    return (int(hex_a, 16) ^ int(hex_b, 16)).bit_count()


def build_duplicate_signature(order: Order, receipt_data: dict | None = None) -> str:
    if not order.check_image:
        return ''

    image_bytes = _normalized_image_bytes(order.check_image.path)
    payload = (f'user:{order.user_id}|cafe:{order.cafe_id}|').encode() + image_bytes
    return hashlib.sha256(payload).hexdigest()


def build_content_signature(receipt_data: dict | None) -> str:
    data = receipt_data or {}

    payload = {
        'cafe_name': _clean_text(data.get('cafe_name')),
        'receipt_date': _normalized_date_key(data.get('receipt_date')),
        'total_amount': _normalized_decimal(data.get('total_amount')),
        'receipt_number': _digits_only(data.get('receipt_number')),
        'fiscal_number': _digits_only(data.get('fiscal_number')),
        'items': _normalized_text_block(_item_names_from_data(data)),
    }
    payload = {key: value for key, value in payload.items() if value}

    if len(payload) < 3:
        return ''

    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def find_exact_duplicate(order: Order) -> Order | None:
    if not order.check_sha256:
        return None

    return (
        Order.objects.filter(check_sha256=order.check_sha256)
        .exclude(pk=order.pk)
        .order_by('created_at', 'pk')
        .first()
    )


def _same_total(a: Any, b: Any) -> bool:
    da = _decimal_or_none(a)
    db = _decimal_or_none(b)
    if da is None or db is None:
        return False
    return da == db


def _same_place(order: Order, candidate: Order) -> bool:
    if order.cafe_id and candidate.cafe_id:
        return order.cafe_id == candidate.cafe_id

    order_place = _normalized_text_block(order.place_name)
    candidate_place = _normalized_text_block(candidate.place_name)
    return bool(order_place and candidate_place and order_place == candidate_place)


def _same_receipt_numbers(order: Order, candidate: Order) -> bool:
    receipt_match = (
        bool(order.receipt_number)
        and bool(candidate.receipt_number)
        and _digits_only(order.receipt_number) == _digits_only(candidate.receipt_number)
    )
    fiscal_match = (
        bool(order.fiscal_number)
        and bool(candidate.fiscal_number)
        and _digits_only(order.fiscal_number) == _digits_only(candidate.fiscal_number)
    )
    return receipt_match or fiscal_match


def _same_date_and_total(order: Order, candidate: Order) -> bool:
    same_date = (
        bool(order.receipt_date)
        and bool(candidate.receipt_date)
        and _normalized_date_key(order.receipt_date) == _normalized_date_key(candidate.receipt_date)
    )
    same_total = _same_total(order.total_sum, candidate.total_sum)
    return same_date and same_total


def _content_duplicate_score(order: Order, candidate: Order) -> int:
    score = 0

    if _same_receipt_numbers(order, candidate):
        score += 8
    if _same_place(order, candidate):
        score += 3
    if _same_date_and_total(order, candidate):
        score += 5

    order_tokens = _fingerprint_tokens(
        order.parsed_data if isinstance(order.parsed_data, dict) else {}
    )
    candidate_tokens = _fingerprint_tokens(
        candidate.parsed_data if isinstance(candidate.parsed_data, dict) else {}
    )
    token_similarity = _token_similarity(order_tokens, candidate_tokens)
    if token_similarity >= TOKEN_SIMILARITY_THRESHOLD:
        score += 4

    current_raw = _raw_summary_from_data(
        order.parsed_data if isinstance(order.parsed_data, dict) else {}
    )
    candidate_raw = _raw_summary_from_data(
        candidate.parsed_data if isinstance(candidate.parsed_data, dict) else {}
    )
    if current_raw and candidate_raw and current_raw == candidate_raw:
        score += 4

    return score


def _find_text_duplicate(order: Order) -> Order | None:
    queryset = Order.objects.exclude(pk=order.pk)

    if order.cafe_id:
        queryset = queryset.filter(cafe_id=order.cafe_id)
    elif order.place_name:
        queryset = queryset.filter(place_name__iexact=order.place_name)

    if order.total_sum is not None:
        queryset = queryset.filter(total_sum=order.total_sum)

    candidates = queryset.only(
        'id',
        'parsed_data',
        'created_at',
        'cafe_id',
        'place_name',
        'total_sum',
        'receipt_date',
        'receipt_number',
        'fiscal_number',
    ).order_by('created_at', 'pk')[:100]

    best_match: Order | None = None
    best_score = 0

    for candidate in candidates:
        score = _content_duplicate_score(order, candidate)
        if score >= 8 and score > best_score:
            best_match = candidate
            best_score = score

    return best_match


def find_content_duplicate(order: Order) -> Order | None:
    base_qs = Order.objects.exclude(pk=order.pk)

    if order.receipt_number:
        candidate = (
            base_qs.filter(receipt_number=order.receipt_number).order_by('created_at', 'pk').first()
        )
        if candidate:
            return candidate

    if order.fiscal_number:
        candidate = (
            base_qs.filter(fiscal_number=order.fiscal_number).order_by('created_at', 'pk').first()
        )
        if candidate:
            return candidate

    if order.content_signature:
        queryset = base_qs.filter(content_signature=order.content_signature)
        if order.cafe_id:
            queryset = queryset.filter(cafe_id=order.cafe_id)

        candidate = queryset.order_by('created_at', 'pk').first()
        if candidate:
            return candidate

    queryset = base_qs
    if order.cafe_id:
        queryset = queryset.filter(cafe_id=order.cafe_id)
    elif order.place_name:
        queryset = queryset.filter(place_name__iexact=order.place_name)

    if order.receipt_date:
        queryset = queryset.filter(receipt_date=order.receipt_date)

    if order.total_sum is not None:
        queryset = queryset.filter(total_sum=order.total_sum)

    candidate = queryset.order_by('created_at', 'pk').first()
    if candidate:
        return candidate

    filters = Q()
    if order.cafe_id:
        filters &= Q(cafe_id=order.cafe_id)
    elif order.place_name:
        filters &= Q(place_name__iexact=order.place_name)

    if order.receipt_date:
        filters &= Q(receipt_date=order.receipt_date)

    if order.total_sum is not None:
        filters &= Q(total_sum=order.total_sum)

    fallback_qs = base_qs.filter(filters) if filters else base_qs

    for candidate in fallback_qs.only(
        'id',
        'cafe_id',
        'place_name',
        'receipt_date',
        'receipt_number',
        'fiscal_number',
        'total_sum',
        'created_at',
        'parsed_data',
    ).order_by('created_at', 'pk')[:50]:
        if _same_receipt_numbers(order, candidate):
            return candidate
        if _same_place(order, candidate) and _same_date_and_total(order, candidate):
            return candidate
        if _content_duplicate_score(order, candidate) >= 8:
            return candidate

    text_duplicate = _find_text_duplicate(order)
    if text_duplicate:
        return text_duplicate

    return None


def find_similar_image_duplicate(
    order: Order, max_distance: int = DHASH_MAX_DISTANCE
) -> Order | None:
    if not order.check_image:
        return None

    current_variants = image_hash_variants(order.check_image.path)
    if not current_variants:
        return None

    queryset = Order.objects.exclude(pk=order.pk).exclude(check_image='')

    if order.cafe_id:
        queryset = queryset.filter(cafe_id=order.cafe_id)
    elif order.place_name:
        queryset = queryset.filter(place_name__iexact=order.place_name)

    if order.total_sum is not None:
        queryset = queryset.filter(total_sum=order.total_sum)

    candidates = queryset.only(
        'id',
        'check_image',
        'created_at',
        'cafe_id',
        'place_name',
        'receipt_date',
        'total_sum',
    ).order_by('created_at', 'pk')[:100]

    best_match: Order | None = None
    best_distance: int | None = None

    for candidate in candidates:
        try:
            candidate_variants = image_hash_variants(candidate.check_image.path)
        except Exception as exc:
            logger.debug('Пропуск кандидата #%s при хешировании: %s', candidate.pk, exc)
            continue

        for current_kind, current_hash in current_variants:
            for candidate_kind, candidate_hash in candidate_variants:
                if current_kind != candidate_kind:
                    continue
                distance = hamming_distance(current_hash, candidate_hash)
                limit = DHASH_MAX_DISTANCE if current_kind == 'd' else AHASH_MAX_DISTANCE
                if distance <= limit and (best_distance is None or distance < best_distance):
                    best_match = candidate
                    best_distance = distance

    return best_match

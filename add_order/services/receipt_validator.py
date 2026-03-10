from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .receipt_ai import analyze_receipt
from .receipt_duplicates import (
    build_content_signature,
    build_duplicate_signature,
    file_sha256,
    find_content_duplicate,
    find_exact_duplicate,
    find_similar_image_duplicate,
    image_dhash,
)
from .receipt_matcher import match_items


def _clean_text(value: Any) -> str:
    return ' '.join(str(value or '').strip().split())


def _to_decimal_or_none(value: Any) -> Decimal | None:
    if value in (None, '', 'null'):
        return None
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _mark_duplicate(order, source_order, reason: str):
    order.is_duplicate = True
    order.duplicate_reason = reason
    order.duplicate_source_order = source_order
    order.save(update_fields=['is_duplicate', 'duplicate_reason', 'duplicate_source_order'])
    return order


def process_order_receipt(order):
    if not order.check_image:
        return None

    if not order.check_sha256:
        order.check_sha256 = file_sha256(order.check_image.path)

    if not order.check_dhash:
        order.check_dhash = image_dhash(order.check_image.path)

    if not order.duplicate_signature:
        order.duplicate_signature = build_duplicate_signature(order)

    order.save(update_fields=['check_sha256', 'check_dhash', 'duplicate_signature'])

    exact_duplicate = find_exact_duplicate(order)
    if exact_duplicate:
        _mark_duplicate(order, exact_duplicate, order.DuplicateReason.EXACT_IMAGE)
        return order.parsed_data

    data = analyze_receipt(order.check_image.path) or {}

    place_name = _clean_text(data.get('cafe_name'))
    receipt_date = _clean_text(data.get('receipt_date'))
    receipt_time = _clean_text(data.get('receipt_time'))
    receipt_number = _clean_text(data.get('receipt_number'))
    fiscal_number = _clean_text(data.get('fiscal_number'))
    total_sum = _to_decimal_or_none(data.get('total_amount'))

    order.parsed_data = data if isinstance(data, dict) else {}
    if place_name:
        order.place_name = place_name
    order.total_sum = total_sum
    order.receipt_date = receipt_date
    order.receipt_time = receipt_time
    order.receipt_number = receipt_number
    order.fiscal_number = fiscal_number

    items = order.parsed_data.get('items', [])
    matches, matched_total = match_items(items, order.cafe)
    order.parsed_data['matches'] = matches
    order.parsed_data['matched_total'] = matched_total

    order.parsed_data['cafe_name'] = order.place_name or order.parsed_data.get('cafe_name')
    order.parsed_data['receipt_date'] = order.receipt_date
    order.parsed_data['receipt_time'] = order.receipt_time
    order.parsed_data['receipt_number'] = order.receipt_number
    order.parsed_data['fiscal_number'] = order.fiscal_number
    order.parsed_data['total_amount'] = (
        float(order.total_sum)
        if order.total_sum is not None
        else order.parsed_data.get('total_amount')
    )

    order.content_signature = build_content_signature(order.parsed_data)

    order.save(
        update_fields=[
            'parsed_data',
            'place_name',
            'total_sum',
            'receipt_date',
            'receipt_time',
            'receipt_number',
            'fiscal_number',
            'content_signature',
        ]
    )

    content_duplicate = find_content_duplicate(order)
    if content_duplicate:
        _mark_duplicate(order, content_duplicate, order.DuplicateReason.CONTENT_MATCH)
        return order.parsed_data

    similar_duplicate = find_similar_image_duplicate(order)
    if similar_duplicate:
        _mark_duplicate(order, similar_duplicate, order.DuplicateReason.IMAGE_SIMILAR)
        return order.parsed_data

    order.is_duplicate = False
    order.duplicate_reason = ''
    order.duplicate_source_order = None
    order.save(update_fields=['is_duplicate', 'duplicate_reason', 'duplicate_source_order'])

    return order.parsed_data

from .receipt_ai import analyze_receipt
from .receipt_matcher import match_items


def process_order_receipt(order):
    if not order.check_image:
        return None

    if order.parsed_data:
        return order.parsed_data

    data = analyze_receipt(order.check_image.path)

    order.parsed_data = data
    order.total_sum = data.get('total_amount')

    items = data.get('items', [])
    matches, matched_total = match_items(items, order.cafe)

    order.parsed_data['matches'] = matches
    order.parsed_data['matched_total'] = matched_total

    order.save(update_fields=['parsed_data', 'total_sum'])

    return order.parsed_data

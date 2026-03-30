from django.db import migrations


NEW_COUPONS = [
    # ── COMMON ──────────────────────────────────────────────────────────────
    {
        "title": "Американо",
        "description": "Большой американо в любом кафе-партнёре",
        "reward_type": "COFFEE",
        "rarity": "COMMON",
        "cost_points10": 1300,
        "available_in_shop": True,
        "available_in_drop": True,
        "expires_in_days": 7,
    },
    {
        "title": "Горячий шоколад",
        "description": "Согревающий горячий шоколад",
        "reward_type": "DRINK",
        "rarity": "COMMON",
        "cost_points10": 850,
        "available_in_shop": True,
        "available_in_drop": True,
        "expires_in_days": 7,
    },
    {
        "title": "Скидка 50₽",
        "description": "Скидка 50 рублей на любой заказ",
        "reward_type": "DISCOUNT",
        "rarity": "COMMON",
        "cost_points10": 600,
        "available_in_shop": True,
        "available_in_drop": True,
        "expires_in_days": 5,
    },
    # ── RARE ────────────────────────────────────────────────────────────────
    {
        "title": "Скидка 350₽",
        "description": "Скидка 350 рублей на заказ",
        "reward_type": "DISCOUNT",
        "rarity": "RARE",
        "cost_points10": 4000,
        "available_in_shop": True,
        "available_in_drop": True,
        "expires_in_days": 10,
    },
    {
        "title": "Кофе + десерт",
        "description": "Кофе любого размера и десерт на выбор",
        "reward_type": "COMBO",
        "rarity": "RARE",
        "cost_points10": 2300,
        "available_in_shop": True,
        "available_in_drop": True,
        "expires_in_days": 10,
    },
    {
        "title": "Молочный коктейль",
        "description": "Фирменный молочный коктейль",
        "reward_type": "DRINK",
        "rarity": "RARE",
        "cost_points10": 1900,
        "available_in_shop": True,
        "available_in_drop": True,
        "expires_in_days": 10,
    },
    # ── LEGENDARY ───────────────────────────────────────────────────────────
    {
        "title": "Завтрак на двоих",
        "description": "Полноценный завтрак на двух человек",
        "reward_type": "COMBO",
        "rarity": "LEGENDARY",
        "cost_points10": 0,
        "available_in_shop": False,
        "available_in_drop": True,
        "expires_in_days": 14,
    },
    {
        "title": "Паста дня",
        "description": "Порция фирменной пасты по выбору шефа",
        "reward_type": "MEAL",
        "rarity": "LEGENDARY",
        "cost_points10": 0,
        "available_in_shop": False,
        "available_in_drop": True,
        "expires_in_days": 14,
    },
    {
        "title": "Торт именинника",
        "description": "Целый торт от кафе-партнёра",
        "reward_type": "DESSERT",
        "rarity": "LEGENDARY",
        "cost_points10": 0,
        "available_in_shop": False,
        "available_in_drop": True,
        "expires_in_days": 14,
    },
]


def seed_coupons(apps, schema_editor):
    CouponOffer = apps.get_model("promo", "CouponOffer")
    for data in NEW_COUPONS:
        CouponOffer.objects.get_or_create(
            title=data["title"],
            defaults=data,
        )


def unseed_coupons(apps, schema_editor):
    CouponOffer = apps.get_model("promo", "CouponOffer")
    titles = [c["title"] for c in NEW_COUPONS]
    CouponOffer.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            "promo",
            "0005_rename_promo_coupo_is_acti_34e10a_idx_promo_coupo_is_acti_75c4b6_idx_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(seed_coupons, reverse_code=unseed_coupons),
    ]

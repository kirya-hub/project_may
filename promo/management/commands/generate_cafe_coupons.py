import random

from django.core.management.base import BaseCommand, CommandError

from cafes.models import Cafe, MenuItem
from promo.models import CouponOffer


RARITY_CONFIGS = (
    {
        'rarity': CouponOffer.Rarity.COMMON,
        'title': 'Скидка на {name}',
        'description': 'Скидка на фирменное блюдо: {name}',
        'cost_points10': 500,
        'expires_in_days': 7,
        'fallback_reward_type': CouponOffer.RewardType.DISCOUNT,
    },
    {
        'rarity': CouponOffer.Rarity.RARE,
        'title': '{name}',
        'description': 'Фирменный купон на позицию меню: {name}',
        'cost_points10': 2000,
        'expires_in_days': 10,
        'fallback_reward_type': CouponOffer.RewardType.MEAL,
    },
    {
        'rarity': CouponOffer.Rarity.LEGENDARY,
        'title': '{name}',
        'description': 'Особый купон от кафе на фирменную позицию: {name}',
        'cost_points10': 5000,
        'expires_in_days': 14,
        'fallback_reward_type': CouponOffer.RewardType.COMBO,
    },
)

COFFEE_KEYWORDS = (
    'кофе',
    'американо',
    'капучино',
    'латте',
    'эспрессо',
)
DRINK_KEYWORDS = (
    'чай',
    'лимонад',
    'коктейль',
    'сок',
    'напиток',
    'морс',
)
DESSERT_KEYWORDS = (
    'десерт',
    'торт',
    'чизкейк',
    'пирожное',
    'круассан',
    'булочка',
    'печенье',
)


class Command(BaseCommand):
    help = 'Создает фирменные купоны для кафе на основе позиций меню'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, какие купоны будут созданы, без записи в базу',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Игнорировать проверку существующих купонов для cafe + menu_item',
        )
        parser.add_argument(
            '--cafe-id',
            type=int,
            help='Создать купоны только для указанного кафе',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        cafe_id = options.get('cafe_id')

        cafes = Cafe.objects.all().order_by('id')
        if cafe_id is not None:
            cafes = cafes.filter(pk=cafe_id)
            if not cafes.exists():
                raise CommandError(f'Кафе с id={cafe_id} не найдено.')

        created_count = 0
        skipped_cafes = 0
        skipped_duplicates = 0

        for cafe in cafes:
            self.stdout.write(f'Кафе: {cafe.name}')

            menu_items = list(
                MenuItem.objects.filter(category__cafe=cafe).select_related('category')
            )
            if not menu_items:
                skipped_cafes += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'{cafe.name}: нет позиций меню, кафе пропущено'
                    )
                )
                continue

            if force:
                candidate_items = menu_items[:]
            else:
                existing_item_ids = set(
                    CouponOffer.objects.filter(cafe=cafe, menu_item__isnull=False)
                    .values_list('menu_item_id', flat=True)
                )
                skipped_duplicates += len(existing_item_ids.intersection(item.id for item in menu_items))
                candidate_items = [
                    item for item in menu_items if item.id not in existing_item_ids
                ]

            random.shuffle(candidate_items)
            selected_items = candidate_items[: min(3, len(candidate_items))]

            if not selected_items:
                skipped_cafes += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'{cafe.name}: свободных позиций меню без дублей не найдено, кафе пропущено'
                    )
                )
                continue

            used_item_ids = set()
            cafe_created = 0

            for rarity_config in RARITY_CONFIGS:
                menu_item = next(
                    (
                        item for item in selected_items
                        if item.id not in used_item_ids
                    ),
                    None,
                )
                if menu_item is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f'{cafe.name}: недостаточно свободных позиций меню для всех редкостей'
                        )
                    )
                    break

                used_item_ids.add(menu_item.id)
                reward_type = self._resolve_reward_type(
                    menu_item.name,
                    fallback=rarity_config['fallback_reward_type'],
                )
                title = rarity_config['title'].format(name=menu_item.name)

                coupon_data = {
                    'title': title,
                    'description': rarity_config['description'].format(name=menu_item.name),
                    'reward_type': reward_type,
                    'rarity': rarity_config['rarity'],
                    'cafe': cafe,
                    'menu_item': menu_item,
                    'image': None,
                    'cost_points10': rarity_config['cost_points10'],
                    'available_in_shop': True,
                    'available_in_drop': True,
                    'expires_in_days': rarity_config['expires_in_days'],
                    'is_active': True,
                }

                if dry_run:
                    created_count += 1
                else:
                    CouponOffer.objects.create(**coupon_data)
                    created_count += 1

                cafe_created += 1
                self.stdout.write(
                    f'{cafe.name}: создан {rarity_config["rarity"]} купон "{title}" '
                    f'для блюда "{menu_item.name}"'
                )

            if cafe_created == 0:
                skipped_cafes += 1

        self.stdout.write(f'Создано купонов: {created_count}')
        self.stdout.write(f'Пропущено кафе: {skipped_cafes}')
        self.stdout.write(f'Пропущено блюд из-за дублей: {skipped_duplicates}')

    def _resolve_reward_type(self, menu_item_name, fallback):
        normalized_name = menu_item_name.lower()

        if any(keyword in normalized_name for keyword in COFFEE_KEYWORDS):
            return CouponOffer.RewardType.COFFEE
        if any(keyword in normalized_name for keyword in DRINK_KEYWORDS):
            return CouponOffer.RewardType.DRINK
        if any(keyword in normalized_name for keyword in DESSERT_KEYWORDS):
            return CouponOffer.RewardType.DESSERT
        return fallback

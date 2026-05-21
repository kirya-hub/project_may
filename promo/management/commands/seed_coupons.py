from django.core.management.base import BaseCommand

from cafes.models import Cafe, MenuItem
from promo.models import CouponOffer

COUPON_TEMPLATES = [
    {
        'title': 'Бесплатный кофе',
        'menu_item_name': 'Татарский раф',
        'description': 'Бесплатный Татарский раф при следующем визите',
        'reward_type': CouponOffer.RewardType.COFFEE,
        'rarity': CouponOffer.Rarity.COMMON,
        'cost_points10': 100,
    },
    {
        'title': 'Скидка 15% на завтрак',
        'menu_item_name': 'Фермерский завтрак',
        'description': 'Скидка 15% на Фермерский завтрак',
        'reward_type': CouponOffer.RewardType.DISCOUNT,
        'rarity': CouponOffer.Rarity.COMMON,
        'cost_points10': 100,
    },
    {
        'title': 'Бесплатный напиток',
        'menu_item_name': 'Орео милкшейк',
        'description': 'Бесплатный Орео милкшейк',
        'reward_type': CouponOffer.RewardType.DRINK,
        'rarity': CouponOffer.Rarity.COMMON,
        'cost_points10': 100,
    },
    {
        'title': 'Бесплатная пицца',
        'menu_item_name': 'Маргарита 27',
        'description': 'Бесплатная пицца Маргарита 27 см',
        'reward_type': CouponOffer.RewardType.MEAL,
        'rarity': CouponOffer.Rarity.RARE,
        'cost_points10': 250,
    },
    {
        'title': 'Десерт в подарок',
        'menu_item_name': 'Наполеон',
        'description': 'Бесплатный десерт на выбор',
        'reward_type': CouponOffer.RewardType.DESSERT,
        'rarity': CouponOffer.Rarity.RARE,
        'cost_points10': 250,
    },
    {
        'title': 'Комбо завтрак + кофе',
        'menu_item_name': 'Хашбраун завтрак',
        'description': 'Хашбраун завтрак + любой напиток бесплатно',
        'reward_type': CouponOffer.RewardType.COMBO,
        'rarity': CouponOffer.Rarity.LEGENDARY,
        'cost_points10': 500,
    },
]


class Command(BaseCommand):
    help = 'Пересоздать купоны Coffee Cava, привязанные к блюдам меню'

    def handle(self, *args, **options):
        try:
            coffee_cava = Cafe.objects.get(name__icontains='Coffee Cava')
        except Cafe.DoesNotExist:
            self.stderr.write('Кафе Coffee Cava не найдено.')
            return

        deleted, _ = CouponOffer.objects.all().delete()
        self.stdout.write(f'Удалено купонов: {deleted}')

        all_items = list(MenuItem.objects.filter(category__cafe=coffee_cava))
        created = []

        for tmpl in COUPON_TEMPLATES:
            menu_item = next(
                (i for i in all_items if tmpl['menu_item_name'].lower() in i.name.lower()),
                None,
            )
            if menu_item is None:
                self.stderr.write(
                    f'  [!] Блюдо "{tmpl["menu_item_name"]}" не найдено — купон "{tmpl["title"]}" пропущен'
                )
                continue

            obj = CouponOffer.objects.create(
                cafe=coffee_cava,
                title=tmpl['title'],
                description=tmpl['description'],
                reward_type=tmpl['reward_type'],
                rarity=tmpl['rarity'],
                cost_points10=tmpl['cost_points10'],
                menu_item=menu_item,
                available_in_shop=True,
                available_in_drop=True,
                is_active=True,
                expires_in_days=30,
            )
            created.append(obj)
            self.stdout.write(f'  [{obj.rarity}] {obj.title} → {menu_item.name}')

        self.stdout.write(self.style.SUCCESS(f'Готово. Создано: {len(created)} купонов.'))

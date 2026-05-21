from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Очищает все промо-данные: купоны, транзакции, промокоды, дропы'

    def handle(self, *args, **options):
        from user_profile.models import PromoCode
        from promo.models import CouponOffer, PointsTransaction

        try:
            from trades.models import TradeItem
            ti = TradeItem.objects.all().delete()
            self.stdout.write(f'  TradeItem: {ti[0]} удалено')
        except Exception as e:
            self.stdout.write(f'  TradeItem: пропущено ({e})')

        try:
            from trades.models import Trade
            tr = Trade.objects.all().delete()
            self.stdout.write(f'  Trade: {tr[0]} удалено')
        except Exception as e:
            self.stdout.write(f'  Trade: пропущено ({e})')

        pc = PromoCode.objects.all().delete()
        pt = PointsTransaction.objects.all().delete()

        try:
            from drops.models import DropOption, DropWeek
            do = DropOption.objects.all().delete()
            dw = DropWeek.objects.all().delete()
            self.stdout.write(f'  DropOption: {do[0]} удалено')
            self.stdout.write(f'  DropWeek: {dw[0]} удалено')
        except Exception as e:
            self.stdout.write(f'  Дропы: пропущено ({e})')

        co = CouponOffer.objects.all().delete()

        self.stdout.write(f'  PromoCode: {pc[0]} удалено')
        self.stdout.write(f'  PointsTransaction: {pt[0]} удалено')
        self.stdout.write(f'  CouponOffer: {co[0]} удалено')
        self.stdout.write(self.style.SUCCESS('Готово. База промо очищена.'))

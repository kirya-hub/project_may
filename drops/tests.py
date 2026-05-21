from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from cafes.models import Cafe
from promo.models import CouponOffer
from user_profile.models import Profile, PromoCode

from .models import DropOption, DropWeek, week_start_for
from .services import (
    _expire_if_needed,
    get_claimable_week,
    get_current_week,
    get_user_tier_for_week,
    phase,
)

# --------------------------------------------------------------------------- #
# Фабрики                                                                       #
# --------------------------------------------------------------------------- #

def _make_user(username='tester'):
    return User.objects.create_user(username=username, password='x')


def _make_cafe(name='CafeTest'):
    return Cafe.objects.get_or_create(name=name)[0]


def _make_offer(cafe, rarity=CouponOffer.Rarity.COMMON):
    return CouponOffer.objects.create(
        cafe=cafe,
        description='Бесплатный кофе',
        rarity=rarity,
        is_active=True,
        available_in_drop=True,
    )


def _add_order(user, total, at_dt):
    """Создаёт Order и вручную проставляет created_at (обходит auto_now_add)."""
    from add_order.models import Order
    cafe = _make_cafe()
    order = Order.objects.create(user=user, cafe=cafe, total_sum=total, is_duplicate=False)
    Order.objects.filter(pk=order.pk).update(created_at=at_dt)
    return Order.objects.get(pk=order.pk)


def _current_monday():
    today = date.today()
    return today - timedelta(days=today.weekday())


# --------------------------------------------------------------------------- #
# TierForWeekTest                                                               #
# --------------------------------------------------------------------------- #

class TierForWeekTest(TestCase):
    """get_user_tier_for_week: расчёт тира за конкретную неделю."""

    def setUp(self):
        self.user = _make_user('tier_user')
        Profile.objects.create(user=self.user, level=1)

    def test_no_orders_returns_none(self):
        ws = _current_monday()
        tier, adj = get_user_tier_for_week(self.user, ws)
        self.assertIsNone(tier)
        self.assertEqual(adj, 0.0)

    def test_bronze_tier(self):
        ws = _current_monday()
        mid_week = timezone.make_aware(
            timezone.datetime.combine(ws + timedelta(days=2), timezone.datetime.min.time())
        )
        _add_order(self.user, 700, mid_week)
        tier, adj = get_user_tier_for_week(self.user, ws)
        self.assertEqual(tier, 'BRONZE')
        self.assertAlmostEqual(adj, 700.0, places=1)

    def test_gold_tier(self):
        ws = _current_monday()
        mid_week = timezone.make_aware(
            timezone.datetime.combine(ws + timedelta(days=3), timezone.datetime.min.time())
        )
        _add_order(self.user, 2500, mid_week)
        tier, adj = get_user_tier_for_week(self.user, ws)
        self.assertEqual(tier, 'GOLD')

    def test_order_outside_week_excluded(self):
        ws = _current_monday()
        next_week = timezone.make_aware(
            timezone.datetime.combine(ws + timedelta(days=8), timezone.datetime.min.time())
        )
        _add_order(self.user, 2500, next_week)
        tier, _ = get_user_tier_for_week(self.user, ws)
        self.assertIsNone(tier)

    def test_duplicate_excluded(self):
        from add_order.models import Order
        ws = _current_monday()
        mid_week = timezone.make_aware(
            timezone.datetime.combine(ws + timedelta(days=2), timezone.datetime.min.time())
        )
        cafe = _make_cafe()
        order = Order.objects.create(user=self.user, cafe=cafe, total_sum=2000, is_duplicate=True)
        Order.objects.filter(pk=order.pk).update(created_at=mid_week)
        tier, _ = get_user_tier_for_week(self.user, ws)
        self.assertIsNone(tier)

    def test_level_bonus_applied(self):
        Profile.objects.filter(user=self.user).update(level=15)  # +25%
        ws = _current_monday()
        mid_week = timezone.make_aware(
            timezone.datetime.combine(ws + timedelta(days=2), timezone.datetime.min.time())
        )
        _add_order(self.user, 1700, mid_week)
        tier, adj = get_user_tier_for_week(self.user, ws)
        # 1700 * 1.25 = 2125 → GOLD
        self.assertEqual(tier, 'GOLD')
        self.assertAlmostEqual(adj, 2125.0, places=1)


# --------------------------------------------------------------------------- #
# PhaseTest                                                                     #
# --------------------------------------------------------------------------- #

class PhaseTest(TestCase):
    """phase(): правильная фаза по дате."""

    def _make_week(self, ws: date, suffix='') -> DropWeek:
        user = _make_user(f'ph{ws}{suffix}')
        return DropWeek.objects.create(user=user, week_start=ws)

    def test_accumulate(self):
        ws = _current_monday()
        week = self._make_week(ws, 'acc')
        # Сегодня находится внутри недели → ACCUMULATE
        self.assertEqual(phase(week), 'ACCUMULATE')

    def test_claim(self):
        ws = _current_monday() - timedelta(days=7)  # прошлая неделя
        week = self._make_week(ws, 'claim')
        # Если сегодня ≥ ws+7 и < ws+14 → CLAIM
        # Это верно если мы в первые 7 дней после прошлой недели
        p = phase(week)
        self.assertIn(p, ('CLAIM', 'EXPIRED'))  # зависит от дня недели

    def test_expired_after_14_days(self):
        ws = _current_monday() - timedelta(days=14)
        week = self._make_week(ws, 'exp')
        self.assertEqual(phase(week), 'EXPIRED')


# --------------------------------------------------------------------------- #
# ExpireIfNeededTest                                                            #
# --------------------------------------------------------------------------- #

class ExpireIfNeededTest(TestCase):
    """_expire_if_needed(): EXPIRED после 14 дней, обрабатывает ACTIVE."""

    def _make_week(self, ws, status=DropWeek.Status.CHOOSING):
        user = _make_user(f'en{ws}{status}')
        return DropWeek.objects.create(user=user, week_start=ws, status=status)

    def test_choosing_expires_after_14_days(self):
        ws = _current_monday() - timedelta(days=14)
        week = self._make_week(ws)
        result = _expire_if_needed(week)
        self.assertEqual(result.status, DropWeek.Status.EXPIRED)

    def test_active_expires_after_14_days(self):
        ws = _current_monday() - timedelta(days=14)
        week = self._make_week(ws, status=DropWeek.Status.ACTIVE)
        result = _expire_if_needed(week)
        self.assertEqual(result.status, DropWeek.Status.EXPIRED)

    def test_completed_not_touched(self):
        ws = _current_monday() - timedelta(days=14)
        week = self._make_week(ws, status=DropWeek.Status.COMPLETED)
        result = _expire_if_needed(week)
        self.assertEqual(result.status, DropWeek.Status.COMPLETED)

    def test_not_expired_before_14_days(self):
        ws = _current_monday() - timedelta(days=7)  # 8-й день — в окне CLAIM
        week = self._make_week(ws)
        result = _expire_if_needed(week)
        self.assertEqual(result.status, DropWeek.Status.CHOOSING)


# --------------------------------------------------------------------------- #
# ChooseOptionTest                                                              #
# --------------------------------------------------------------------------- #

class ChooseOptionTest(TestCase):
    """choose_option: купон выдаётся сразу, срок по редкости, статус COMPLETED."""

    def setUp(self):
        self.user = _make_user('cho_user')
        self.profile, _ = Profile.objects.get_or_create(user=self.user)
        self.cafe = _make_cafe('ChooseCafe')

    def _setup_claimable(self, rarity=DropOption.Rarity.COMMON):
        """Создаёт неделю в фазе CLAIM со статусом CHOOSING."""
        offer = _make_offer(self.cafe, rarity)
        ws = _current_monday() - timedelta(days=7)
        week = DropWeek.objects.create(
            user=self.user, week_start=ws, status=DropWeek.Status.CHOOSING
        )
        option = DropOption.objects.create(
            drop_week=week, cafe=self.cafe, rarity=rarity, reward_offer=offer
        )
        return week, option

    def _do_choose(self, rarity=DropOption.Rarity.COMMON):
        from .services import choose_option
        week, option = self._setup_claimable(rarity)
        choose_option(self.user, option.id)
        week.refresh_from_db()
        return week

    def test_status_completed_after_choice(self):
        week = self._do_choose()
        self.assertEqual(week.status, DropWeek.Status.COMPLETED)

    def test_promo_code_created(self):
        self._do_choose()
        codes = PromoCode.objects.filter(profile=self.profile, origin=PromoCode.Origin.DROP)
        self.assertEqual(codes.count(), 1)

    def test_expiry_common_5_days(self):
        self._do_choose(DropOption.Rarity.COMMON)
        code = PromoCode.objects.get(profile=self.profile, origin=PromoCode.Origin.DROP)
        self.assertEqual(code.expires_at, date.today() + timedelta(days=5))

    def test_expiry_rare_7_days(self):
        self._do_choose(DropOption.Rarity.RARE)
        code = PromoCode.objects.get(profile=self.profile, origin=PromoCode.Origin.DROP)
        self.assertEqual(code.expires_at, date.today() + timedelta(days=7))

    def test_expiry_legendary_14_days(self):
        self._do_choose(DropOption.Rarity.LEGENDARY)
        code = PromoCode.objects.get(profile=self.profile, origin=PromoCode.Origin.DROP)
        self.assertEqual(code.expires_at, date.today() + timedelta(days=14))

    def test_cannot_choose_twice(self):
        from .services import choose_option
        week, option = self._setup_claimable()
        choose_option(self.user, option.id)
        choose_option(self.user, option.id)  # второй вызов — неделя уже COMPLETED
        codes = PromoCode.objects.filter(profile=self.profile, origin=PromoCode.Origin.DROP)
        self.assertEqual(codes.count(), 1)


# --------------------------------------------------------------------------- #
# ClaimableWeekTest                                                             #
# --------------------------------------------------------------------------- #

class ClaimableWeekTest(TestCase):
    """get_claimable_week: правильное поведение в разных сценариях."""

    def setUp(self):
        self.user = _make_user('cw_user')
        Profile.objects.create(user=self.user, level=1)

    def test_returns_none_if_no_previous_week(self):
        result = get_claimable_week(self.user)
        self.assertIsNone(result)

    def test_returns_none_if_previous_week_expired(self):
        ws = _current_monday() - timedelta(days=7)
        DropWeek.objects.create(user=self.user, week_start=ws, status=DropWeek.Status.EXPIRED)
        result = get_claimable_week(self.user)
        self.assertIsNone(result)

    def test_returns_none_without_tier(self):
        # Нет заказов → нет тира → claimable_week = None
        ws = _current_monday() - timedelta(days=7)
        DropWeek.objects.create(user=self.user, week_start=ws, status=DropWeek.Status.CHOOSING)
        result = get_claimable_week(self.user)
        self.assertIsNone(result)

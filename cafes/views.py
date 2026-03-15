from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from cafes.forms import CafeEditForm
from cafes.models import Cafe, MenuCategory
from feed.models import FeedEvent
from friends.services import friends_qs


def cafes_list(request):
    q = (request.GET.get('q') or '').strip()

    cafes = Cafe.objects.all()

    if q:
        cafes = cafes.filter(name__icontains=q)

    cafes = cafes.annotate(
        checks_count=Count('orders', filter=Q(orders__is_duplicate=False), distinct=True),
        visitors_count=Count('orders__user', filter=Q(orders__is_duplicate=False), distinct=True),
    ).order_by('-checks_count', 'name')

    return render(
        request,
        'cafes/cafes_list.html',
        {
            'cafes': cafes,
            'q': q,
            'show_back': True,
            'header_back_url': reverse('home'),
        },
    )


def cafe_detail(request, slug):
    cafe = get_object_or_404(Cafe, slug=slug)
    can_edit = cafe.can_be_edited_by(request.user)

    orders_qs = cafe.orders.filter(is_duplicate=False)
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    stats = orders_qs.aggregate(
        checks_count=Count('id'),
        visitors_count=Count('user', distinct=True),
        week_checks_count=Count('id', filter=Q(created_at__gte=week_ago)),
        month_visitors_count=Count('user', filter=Q(created_at__gte=month_ago), distinct=True),
        rating_value=Avg('rating', filter=Q(rating__isnull=False)),
        rating_count=Count('id', filter=Q(rating__isnull=False)),
    )

    rating_value = stats['rating_value']
    if rating_value is not None:
        rating_value = round(float(rating_value), 1)

    friend_visitors = []
    if request.user.is_authenticated:
        friend_visitors = (
            friends_qs(request.user)
            .filter(orders__cafe=cafe, orders__is_duplicate=False)
            .select_related('profile')
            .distinct()[:6]
        )

    recent_visits = list(
        orders_qs.select_related('user', 'user__profile').order_by('-created_at')[:6]
    )

    recent_posts = list(
        orders_qs.select_related('user', 'user__profile', 'cafe')
        .prefetch_related('comments')
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
        .order_by('-created_at')[:4]
    )

    recent_events = list(
        FeedEvent.objects.filter(cafe=cafe)
        .select_related('user', 'user__profile')
        .order_by('-created_at')[:4]
    )

    osm_map_url = ''
    if cafe.has_coordinates():
        osm_map_url = (
            'https://www.openstreetmap.org/?'
            + urlencode(
                {
                    'mlat': str(cafe.latitude),
                    'mlon': str(cafe.longitude),
                }
            )
            + f'#map=17/{cafe.latitude}/{cafe.longitude}'
        )

    return render(
        request,
        'cafes/cafe_detail.html',
        {
            'cafe': cafe,
            'can_edit': can_edit,
            'checks_count': stats['checks_count'] or 0,
            'visitors_count': stats['visitors_count'] or 0,
            'week_checks_count': stats['week_checks_count'] or 0,
            'month_visitors_count': stats['month_visitors_count'] or 0,
            'friend_visitors': friend_visitors,
            'recent_visits': recent_visits,
            'recent_posts': recent_posts,
            'recent_events': recent_events,
            'rating_value': rating_value,
            'rating_count': stats['rating_count'] or 0,
            'has_map_coordinates': cafe.has_coordinates(),
            'osm_map_url': osm_map_url,
            'show_back': True,
            'header_back_url': request.GET.get('next') or reverse('cafes_list'),
        },
    )


def category_detail(request, slug, category_slug):
    cafe = get_object_or_404(Cafe, slug=slug)
    category = get_object_or_404(MenuCategory, cafe=cafe, slug=category_slug)
    items = category.items.all()

    return render(
        request,
        'cafes/category_detail.html',
        {
            'cafe': cafe,
            'category': category,
            'items': items,
            'show_back': True,
            'header_back_url': reverse('cafe_detail', args=[cafe.slug]),
        },
    )


@login_required
def cafe_edit(request, slug):
    cafe = get_object_or_404(Cafe, slug=slug)

    if not cafe.can_be_edited_by(request.user):
        raise PermissionDenied

    osm_map_url = ''
    if cafe.has_coordinates():
        osm_map_url = (
            'https://www.openstreetmap.org/?'
            + urlencode(
                {
                    'mlat': str(cafe.latitude),
                    'mlon': str(cafe.longitude),
                }
            )
            + f'#map=17/{cafe.latitude}/{cafe.longitude}'
        )

    if request.method == 'POST':
        form = CafeEditForm(request.POST, request.FILES, instance=cafe)
        if form.is_valid():
            form.save()
            return redirect(f'{reverse("cafe_detail", args=[cafe.slug])}?from=edit')
    else:
        form = CafeEditForm(instance=cafe)

    return render(
        request,
        'cafes/cafe_edit.html',
        {
            'cafe': cafe,
            'form': form,
            'osm_map_url': osm_map_url,
            'show_back': True,
            'header_back_url': reverse('cafe_detail', args=[cafe.slug]),
        },
    )

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from add_order.models import Order
from .models import Like



def feed_home(request):
    qs = Order.objects.select_related("user").order_by("-created_at")

    qs = qs.annotate(likes_count=Count("likes", distinct=True))

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(
                Like.objects.filter(user=request.user, order=OuterRef("pk"))
            )
        )
    else:
        qs = qs.annotate(is_liked=models.Value(False, output_field=models.BooleanField()))

    return render(request, "feed/feed_home.html", {"orders": qs})


@require_POST
@login_required
def toggle_like(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    like, created = Like.objects.get_or_create(user=request.user, order=order)
    if not created:
        like.delete()

    return redirect("home")

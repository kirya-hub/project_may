from django.shortcuts import render, get_object_or_404
from .models import Cafe, MenuCategory


def cafe_detail(request, slug):
    cafe = get_object_or_404(Cafe, slug=slug)
    return render(request, 'cafes/cafe_detail.html', {'cafe': cafe})


def category_detail(request, slug, category_slug):
    cafe = get_object_or_404(Cafe, slug=slug)
    category = get_object_or_404(MenuCategory, slug=category_slug, cafe=cafe)
    items = category.items.all()

    return render(
        request,
        'cafes/category_detail.html',
        {'cafe': cafe, 'category': category, 'items': items},
    )

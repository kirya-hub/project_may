from django.shortcuts import render

def add_order_page(request):
    return render(request, 'add_order/add_order.html')

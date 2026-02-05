from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import OrderForm

@login_required
def add_order_page(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            messages.success(request, "Заказ успешно опубликован!")
            return redirect('add_order')
    else:
        form = OrderForm()

    return render(request, 'add_order/add_order.html', {'form': form})

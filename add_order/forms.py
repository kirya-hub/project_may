from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    """
    Форма для публикации заказа.
    Важно: на уровне UI делаем cafe и total_sum обязательными,
    чтобы начисление баллов и Drop работали стабильно.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Для спринта 3: без кафе и суммы Drop и начисление не сработают
        if 'cafe' in self.fields:
            self.fields['cafe'].required = True
        if 'total_sum' in self.fields:
            self.fields['total_sum'].required = True

    class Meta:
        model = Order
        fields = ('check_image', 'dish_photo', 'comment', 'cafe', 'total_sum')
        widgets = {
            'check_image': forms.ClearableFileInput(
                attrs={
                    'id': 'check_input',
                    'hidden': True,
                    'accept': 'image/*',
                }
            ),
            'dish_photo': forms.ClearableFileInput(
                attrs={
                    'id': 'dish_input',
                    'hidden': True,
                    'accept': 'image/*',
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Комментарий…',
                }
            ),
            'total_sum': forms.NumberInput(
                attrs={
                    'placeholder': 'Сумма чека (₽)',
                    'min': 0,
                    'step': '1',
                }
            ),
        }

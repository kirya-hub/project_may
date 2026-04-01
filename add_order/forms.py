from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    RATING_CHOICES = [
        ('', 'Без оценки'),
        (5, '5 — отлично'),
        (4, '4 — хорошо'),
        (3, '3 — нормально'),
        (2, '2 — слабо'),
        (1, '1 — плохо'),
    ]

    rating = forms.TypedChoiceField(
        choices=RATING_CHOICES,
        coerce=int,
        required=False,
        empty_value=None,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'comment' in self.fields:
            self.fields['comment'].widget.attrs.update({'class': 'comment-input'})

    class Meta:
        model = Order
        fields = ('check_image', 'dish_photo', 'comment', 'rating')
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
        }

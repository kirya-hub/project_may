from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'cafe' in self.fields:
            self.fields['cafe'].required = True

    class Meta:
        model = Order
        fields = ('check_image', 'dish_photo', 'comment', 'cafe')
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

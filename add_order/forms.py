from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['check_image', 'dish_photo', 'comment']
        widgets = {
            'check_image': forms.ClearableFileInput(attrs={
                'id': 'check_input',
                'class': 'file-input',
                'accept': 'image/*'
            }),
            'dish_photo': forms.ClearableFileInput(attrs={
                'id': 'dish_input',
                'class': 'file-input',
                'accept': 'image/*'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'comment-input',
                'placeholder': 'Комментарий...',
            }),
        }

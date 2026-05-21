from django import forms

from .models import Cafe, City


class CafeEditForm(forms.ModelForm):
    class Meta:
        model = Cafe
        fields = [
            'name',
            'avatar',
            'address',
            'city',
            'latitude',
            'longitude',
            'working_hours',
            'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Например: Казань, ул. Баумана, 10',
                }
            ),
            'latitude': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Например: 55.796127',
                    'step': '0.000001',
                }
            ),
            'longitude': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Например: 49.106414',
                    'step': '0.000001',
                }
            ),
            'working_hours': forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Например: 09:00 – 22:00',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-textarea',
                    'rows': 5,
                    'placeholder': 'Коротко расскажите о кафе',
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean() or {}
        address = (cleaned_data.get('address') or '').strip()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if (latitude is None) ^ (longitude is None):
            raise forms.ValidationError('Нужно указать и широту, и долготу вместе.')

        if (latitude is not None or longitude is not None) and not address:
            raise forms.ValidationError('Сначала укажи адрес, потом координаты.')

        return cleaned_data

from django import forms
from .models import Profile


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'name')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ваше имя'}),
        }

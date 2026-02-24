from django import forms

from user_profile.models import PromoCode


class TradeOfferForm(forms.Form):
    offered = forms.ModelMultipleChoiceField(
        queryset=PromoCode.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label='Я отдаю',
    )
    requested = forms.ModelMultipleChoiceField(
        queryset=PromoCode.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label='Я хочу',
    )
    message = forms.CharField(
        max_length=240,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Сообщение (необязательно)',
    )

    def __init__(self, *args, offered_qs=None, requested_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['offered'].queryset = (
            offered_qs if offered_qs is not None else PromoCode.objects.none()
        )
        self.fields['requested'].queryset = (
            requested_qs if requested_qs is not None else PromoCode.objects.none()
        )

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
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Добавь короткое сообщение'}),
        label='Сообщение',
    )

    def __init__(self, *args, offered_qs=None, requested_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['offered'].queryset = (
            offered_qs if offered_qs is not None else PromoCode.objects.none()
        )
        self.fields['requested'].queryset = (
            requested_qs if requested_qs is not None else PromoCode.objects.none()
        )

        self.fields['offered'].label_from_instance = self._coupon_label
        self.fields['requested'].label_from_instance = self._coupon_label

    def _coupon_label(self, coupon):
        offer = getattr(coupon, 'source_offer', None)

        benefit = coupon.description or (offer.description if offer and offer.description else '')
        title = offer.title if offer and offer.title else coupon.code
        rarity = offer.get_rarity_display() if offer else ''
        origin = coupon.get_origin_display() if hasattr(coupon, 'get_origin_display') else ''
        cafe = offer.cafe.name if offer and offer.cafe else ''
        expires = ''
        if getattr(coupon, 'expires_at', None):
            try:
                expires = coupon.expires_at.strftime('%d.%m.%Y')
            except Exception:
                expires = ''

        main = benefit or title
        meta = [title] if benefit and title != benefit else []

        if rarity:
            meta.append(rarity)
        if origin:
            meta.append(origin)
        if cafe:
            meta.append(cafe)
        if expires:
            meta.append(f'до {expires}')

        if meta:
            return f'{main} • {" • ".join(meta)}'
        return main

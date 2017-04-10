from django import forms
from .models import Order


class OrderPictureForm(forms.Form):
    class Meta:
        fields = ['picture']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['picture']

    def __init__(self, *args, **kwargs):
        kwargs['auto_id'] = 'order-%s'
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        for attr in self.initial:
            setattr(self.instance, attr, self.initial[attr])
        return super(OrderForm, self).save(*args, **kwargs)

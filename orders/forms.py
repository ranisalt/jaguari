from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['picture']

    def save(self, *args, **kwargs):
        for attr in self.initial:
            setattr(self.instance, attr, self.initial[attr])
        return super(OrderForm, self).save(*args, **kwargs)

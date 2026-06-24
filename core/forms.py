from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Inquiry


class InquiryForm(forms.ModelForm):
    """«Заявка на расчёт» form. `website` is a hidden honeypot — real users
    never fill it, bots usually do."""

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Inquiry
        fields = ("name", "phone", "message")
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": _("Ваше имя"), "autocomplete": "name",
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "+998 __ ___-__-__", "autocomplete": "tel",
            }),
            "message": forms.Textarea(attrs={
                "placeholder": _("Сообщение (необязательно)"), "rows": 3,
            }),
        }

    def is_spam(self):
        return bool(self.data.get("website"))

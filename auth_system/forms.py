import re
import unicodedata

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


_UKRAINIAN_TRANSLITERATION = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ie', 'ж': 'zh',
    'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'iu', 'я': 'ia', 'є': 'ie', 'ї': 'i',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'H', 'Ґ': 'G', 'Д': 'D', 'Е': 'E', 'Ж': 'Zh', 'З': 'Z',
    'И': 'Y', 'І': 'I', 'Ї': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
    'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch',
    'Ш': 'Sh', 'Щ': 'Shch', 'Ю': 'Iu', 'Я': 'Ia',
}


def _to_ascii(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    result = []
    for char in text:
        if char.isascii():
            result.append(char)
        else:
            result.append(_UKRAINIAN_TRANSLITERATION.get(char, ''))
    return ''.join(result)


def build_username_from_name(first_name, last_name):
    first = _to_ascii((first_name or '').strip()).lower()
    last = _to_ascii((last_name or '').strip()).lower()
    first = re.sub(r'[^a-z0-9]+', '', first)
    last = re.sub(r'[^a-z0-9]+', '', last)
    return '.'.join(part for part in [first, last] if part)


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True, label="Ім'я")
    last_name = forms.CharField(required=True, label="Прізвище")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)

        self.fields["first_name"].widget.attrs.update({"placeholder": "Введіть ім'я"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "Введіть прізвище"})
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Підтвердження пароля"
        self.fields["password1"].widget.attrs.update({"placeholder": "Введіть пароль", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Повторіть пароль", "autocomplete": "new-password"})

    def clean(self):
        cleaned_data = super().clean()
        first_name = (cleaned_data.get("first_name") or "").strip()
        last_name = (cleaned_data.get("last_name") or "").strip()

        if first_name and last_name:
            username = build_username_from_name(first_name, last_name)
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("Користувач з таким ім'ям і прізвищем вже зареєстрований.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        first_name = (self.cleaned_data["first_name"] or "").strip()
        last_name = (self.cleaned_data["last_name"] or "").strip()
        user.username = build_username_from_name(first_name, last_name)
        user.first_name = first_name
        user.last_name = last_name
        user.email = ""
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ("first_name", "last_name", "password1", "password2")
        labels = {
            "first_name": "Ім'я",
            "last_name": "Прізвище",
            "password1": "Пароль",
            "password2": "Підтвердження пароля",
        }
        help_texts = {
            "first_name": "",
            "last_name": "",
            "password1": "",
            "password2": "",
        }

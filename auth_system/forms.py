from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


def build_username_from_name(first_name, last_name):
    return f"{(first_name or '').strip()}.{(last_name or '').strip()}".lower().strip('.')


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




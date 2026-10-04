from django import forms
from django.contrib.auth import get_user_model

from .models import CartOfMenu, RestaurantApplication, RestorantInfo


class RestaurantApplicationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Підтвердження пароля')

    class Meta:
        model = RestaurantApplication
        fields = ['name', 'contact_name', 'phone_number', 'email', 'address', 'opening_hours']
        labels = {
            'name': "Назва ресторану",
            'contact_name': 'Контактна особа',
            'phone_number': 'Телефон',
            'email': 'Email',
            'address': 'Адреса',
            'opening_hours': 'Години роботи',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Наприклад: Green Bistro'}),
            'contact_name': forms.TextInput(attrs={'placeholder': 'Ім’я контактної особи'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+380...'}),
            'email': forms.EmailInput(attrs={'placeholder': 'restaurant@example.com'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Вулиця, номер будинку, місто'}),
            'opening_hours': forms.TextInput(attrs={'placeholder': '10:00-22:00'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Паролі не співпадають.')
        return cleaned_data

    def save(self, commit=True):
        application = super().save(commit=False)
        if not application.owner:
            User = get_user_model()
            username = (application.contact_name or application.name).strip().lower().replace(' ', '_')
            base_username = username or 'restaurant_user'
            final_username = base_username
            counter = 1
            while User.objects.filter(username=final_username).exists():
                final_username = f'{base_username}_{counter}'
                counter += 1

            user = User.objects.create_user(
                username=final_username,
                email=application.email or '',
                password=self.cleaned_data['password'],
                first_name=(application.contact_name or '').split()[0][:30],
                last_name=' '.join((application.contact_name or '').split()[1:])[:30],
            )
            application.owner = user
        if commit:
            application.save()
        return application


class RestorantInfoForm(forms.ModelForm):
    class Meta:
        model = RestorantInfo
        fields = ['name', 'photo', 'address', 'phone_number', 'opening_hours']
        labels = {
            'name': 'Назва ресторану',
            'photo': 'Фото ресторану',
            'address': 'Адреса',
            'phone_number': 'Телефон',
            'opening_hours': 'Години роботи',
        }


class DishForm(forms.ModelForm):
    class Meta:
        model = CartOfMenu
        fields = ['restaurant', 'name', 'photo', 'ingridients', 'weight', 'time_to_cook', 'price']
        labels = {
            'restaurant': 'Ресторан',
            'name': 'Назва страви',
            'photo': 'Фото страви',
            'ingridients': 'Інгредієнти',
            'weight': 'Вага (г)',
            'time_to_cook': 'Час приготування (хв)',
            'price': 'Ціна (₴)',
        }
        widgets = {
            'ingridients': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            restaurants = RestorantInfo.objects.filter(owner=user)
            self.fields['restaurant'].queryset = restaurants
            if restaurants.exists():
                self.initial['restaurant'] = restaurants.first()

from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from .models import CartOfMenu, RestaurantApplication, RestorantInfo


class RestaurantApplicationForm(forms.Form):
    restaurant_name = forms.CharField(max_length=200, label='Назва ресторану')
    contact_first_name = forms.CharField(max_length=100, label="Ім'я контактної особи")
    contact_last_name = forms.CharField(max_length=100, label='Прізвище контактної особи')
    business_type = forms.ChoiceField(
        choices=RestaurantApplication.BUSINESS_TYPE_CHOICES,
        label='Тип магазину/ресторана',
    )
    corporate_email = forms.EmailField(label='Корпоративна email адреса')
    contact_phone = forms.CharField(max_length=25, label='Номер контактної особи')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Підтвердження пароля')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['restaurant_name'].widget.attrs.update({'placeholder': 'Наприклад: Green Bistro'})
        self.fields['contact_first_name'].widget.attrs.update({'placeholder': "Ім'я контактної особи"})
        self.fields['contact_last_name'].widget.attrs.update({'placeholder': 'Прізвище контактної особи'})
        self.fields['contact_phone'].widget.attrs.update({'placeholder': '+380...'})
        self.fields['corporate_email'].widget.attrs.update({'placeholder': 'restaurant@example.com'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Введіть пароль', 'autocomplete': 'new-password'})
        self.fields['confirm_password'].widget.attrs.update({'placeholder': 'Повторіть пароль', 'autocomplete': 'new-password'})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Паролі не співпадають.')

        email = cleaned_data.get('corporate_email')
        if email and RestaurantApplication.objects.filter(corporate_email__iexact=email).exists():
            self.add_error('corporate_email', 'Користувач з такою корпоративною електронною адресою вже зареєстрований.')

        return cleaned_data

    def save(self, commit=True):
        User = get_user_model()
        first_name = (self.cleaned_data['contact_first_name'] or '').strip()
        last_name = (self.cleaned_data['contact_last_name'] or '').strip()
        restaurant_name = (self.cleaned_data['restaurant_name'] or '').strip()
        business_type = self.cleaned_data['business_type']
        corporate_email = self.cleaned_data['corporate_email']
        contact_phone = self.cleaned_data['contact_phone']
        password = self.cleaned_data['password']

        base_username = slugify(f'{first_name} {last_name} {restaurant_name}') or 'restaurant_user'
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}_{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=corporate_email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        application = RestaurantApplication.objects.create(
            owner=user,
            name=restaurant_name,
            contact_name=f'{first_name} {last_name}'.strip(),
            contact_first_name=first_name,
            contact_last_name=last_name,
            business_type=business_type,
            corporate_email=corporate_email,
            contact_phone=contact_phone,
            phone_number=contact_phone,
            email=corporate_email,
            address='',
            opening_hours='',
        )

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


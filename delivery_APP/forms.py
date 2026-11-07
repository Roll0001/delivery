from django import forms

from .models import (
    CITY_CHOICES,
    CartOfMenu,
    COURIER_CITY_CHOICES,
    Delivery,
    Dish,
    ProductType,
    RestaurantApplication,
    RestorantInfo,
)


class RestaurantApplicationForm(forms.Form):
    restaurant_name = forms.CharField(max_length=200, label='Назва ресторану')
    city = forms.ChoiceField(
        choices=[('', 'Оберіть місто'), *CITY_CHOICES],
        label='Місто',
    )
    contact_first_name = forms.CharField(max_length=100, label="Ім'я контактної особи")
    contact_last_name = forms.CharField(max_length=100, label='Прізвище контактної особи')
    business_type = forms.ChoiceField(
        choices=RestaurantApplication.BUSINESS_TYPE_CHOICES,
        label='Тип магазину/ресторана',
    )
    corporate_email = forms.EmailField(label='Корпоративна email адреса')
    contact_phone = forms.CharField(max_length=25, label='Номер контактної особи')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['restaurant_name'].widget.attrs.update({'placeholder': 'Наприклад: Green Bistro'})
        self.fields['contact_first_name'].widget.attrs.update({'placeholder': "Ім'я контактної особи"})
        self.fields['contact_last_name'].widget.attrs.update({'placeholder': 'Прізвище контактної особи'})
        self.fields['contact_phone'].widget.attrs.update({'placeholder': '+380...'})
        self.fields['corporate_email'].widget.attrs.update({'placeholder': 'restaurant@example.com'})

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('corporate_email')
        if email:
            if RestaurantApplication.objects.filter(corporate_email__iexact=email).exists():
                self.add_error(
                    'corporate_email',
                    'Користувач з такою корпоративною електронною адресою вже зареєстрований.',
                )

        return cleaned_data

    def save(self, owner):
        first_name = (self.cleaned_data['contact_first_name'] or '').strip()
        last_name = (self.cleaned_data['contact_last_name'] or '').strip()
        restaurant_name = (self.cleaned_data['restaurant_name'] or '').strip()
        business_type = self.cleaned_data['business_type']
        corporate_email = self.cleaned_data['corporate_email']
        contact_phone = self.cleaned_data['contact_phone']

        application = RestaurantApplication.objects.create(
            owner=owner,
            name=restaurant_name,
            contact_name=f'{first_name} {last_name}'.strip(),
            contact_first_name=first_name,
            contact_last_name=last_name,
            business_type=business_type,
            corporate_email=corporate_email,
            contact_phone=contact_phone,
            city=self.cleaned_data['city'],
            phone_number=contact_phone,
            email=corporate_email,
            address='',
            opening_hours='',
        )
        return application


class RestorantInfoForm(forms.ModelForm):
    photo = forms.ImageField(
        required=False,
        label='Фото закладу',
        help_text='Необов’язково. Можна додати або замінити фото.',
    )

    class Meta:
        model = RestorantInfo
        fields = ['name', 'photo', 'city', 'address', 'phone_number', 'opening_hours']
        labels = {
            'name': 'Назва ресторану або магазину',
            'city': 'Місто',
            'address': 'Адреса',
            'phone_number': 'Телефон',
            'opening_hours': 'Години роботи',
        }


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['name', 'photo', 'dish_type', 'ingridients', 'weight', 'time_to_cook', 'price']
        labels = {
            'name': 'Назва страви',
            'photo': 'Фото страви',
            'dish_type': 'Тип страви',
            'ingridients': 'Інгредієнти',
            'weight': 'Вага',
            'time_to_cook': 'Час приготування (хв)',
            'price': 'Ціна (₴)',
        }
        widgets = {
            'ingridients': forms.Textarea(attrs={'rows': 3}),
        }


class ProductTypeForm(forms.ModelForm):
    class Meta:
        model = ProductType
        fields = ['name', 'photo', 'product_type', 'weight', 'price']
        labels = {
            'name': 'Назва товару',
            'photo': 'Фото товару',
            'product_type': 'Категорія товару',
            'weight': 'Вага або об’єм',
            'price': 'Ціна (₴)',
        }


class MenuDishForm(forms.ModelForm):
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


class OrderForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1, max_value=99, label='Кількість')
    city = forms.ChoiceField(
        choices=[('', 'Оберіть місто доставки'), *COURIER_CITY_CHOICES],
        label='Місто доставки',
    )

    class Meta:
        model = Delivery
        fields = ['name', 'city', 'address', 'phone_number', 'quantity', 'payment_method']
        labels = {
            'name': "Ім'я отримувача",
            'city': 'Місто доставки',
            'address': 'Адреса доставки',
            'phone_number': 'Номер телефону',
            'quantity': 'Кількість',
            'payment_method': 'Спосіб оплати',
        }
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        restaurant_city = kwargs.pop('restaurant_city', '')
        super().__init__(*args, **kwargs)
        valid_cities = {city for city, _label in COURIER_CITY_CHOICES}
        customer_profile = (
            getattr(user, 'customer_profile', None)
            if user and user.is_authenticated
            else None
        )
        customer_city = customer_profile.city if customer_profile else ''
        initial_city = (
            customer_city
            if customer_profile
            else restaurant_city
        )
        if initial_city in valid_cities:
            self.fields['city'].initial = initial_city
        if user and user.is_authenticated:
            self.fields['name'].initial = user.get_full_name() or user.username


class CompletedDeliveryForm(forms.ModelForm):
    completion_photo = forms.ImageField(
        required=True,
        label='Фото підтвердження доставки',
        widget=forms.ClearableFileInput(
            attrs={'accept': 'image/*', 'capture': 'environment'},
        ),
    )

    class Meta:
        model = Delivery
        fields = ['completion_photo']

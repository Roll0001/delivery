from django.shortcuts import render

# Create your views here.


from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from delivery_APP.forms import RestaurantApplicationForm

from .forms import CustomUserCreationForm, build_username_from_name


class EmailAuthenticationForm(AuthenticationForm):
    username = AuthenticationForm.base_fields['username']
    username.widget.attrs.update({'placeholder': 'Введіть ваше Імя та прізвище через крапку'})
    username.label = "Ім'я та прізвище"

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        if username:
            normalized = username.strip()
            if "." not in normalized:
                first_name, last_name = normalized, ""
            else:
                first_name, last_name = normalized.split(".", 1)
            cleaned_data["username"] = build_username_from_name(first_name, last_name)
        return cleaned_data


def register_page(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = CustomUserCreationForm()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='auth_system.backends.EmailBackend')
            return redirect("home")

    return render(request, template_name="register.html", context={"form": form})


def login_page(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = EmailAuthenticationForm()
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='auth_system.backends.EmailBackend')
            return redirect("home")

    return render(request, template_name="login.html", context={"form": form})


def restaurant_login_page(request):
    if request.user.is_authenticated:
        return redirect("restaurant_home")

    form = EmailAuthenticationForm()
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile = getattr(user, 'restaurant_profile', None)
            if not profile or not profile.is_restaurant:
                form.add_error(None, 'Цей обліковий запис не належить ресторану.')
            else:
                login(request, user, backend='auth_system.backends.EmailBackend')
                return redirect("restaurant_home")

    return render(request, template_name="loginforrrestorant.html", context={"form": form})


def restaurant_register_page(request):
    if request.user.is_authenticated:
        return redirect("restaurant_home")

    form = RestaurantApplicationForm()
    if request.method == "POST":
        form = RestaurantApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("restaurant_login")

    return render(request, template_name="registerforrestorant.html", context={"form": form})


def logout_page(request):
    logout(request)
    return redirect("home")
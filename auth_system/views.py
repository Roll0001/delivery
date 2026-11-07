from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET

from delivery_APP.forms import RestaurantApplicationForm
from delivery_APP.models import RestaurantApplication

from .forms import (
    CourierAuthenticationForm,
    CourierCreationForm,
    CustomUserCreationForm,
    build_username_from_name,
)
from .models import CourierProfile, CustomerProfile


class EmailAuthenticationForm(AuthenticationForm):
    username = AuthenticationForm.base_fields['username']
    username.widget.attrs.update({'placeholder': 'Введіть ваше Імя та прізвище через крапку'})
    username.label = "Ім'я та прізвище"

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            normalized = username.strip()
            if "@" in normalized:
                return normalized
            if "." not in normalized:
                first_name, last_name = normalized, ""
            else:
                first_name, last_name = normalized.split(".", 1)
            return build_username_from_name(first_name, last_name)
        return username


def register_page(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = CustomUserCreationForm()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            CustomerProfile.objects.create(user=user, city=form.cleaned_data['city'])
            login(request, user, backend='auth_system.backends.EmailBackend')
            return redirect("home")

    return render(request, template_name="register.html", context={"form": form})


def courier_register_page(request):
    if request.user.is_authenticated:
        return redirect(
            "courier_home"
            if getattr(request.user, 'courier_profile', None)
            else "home"
        )

    form = CourierCreationForm()
    if request.method == "POST":
        form = CourierCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            CourierProfile.objects.create(
                user=user,
                city=form.cleaned_data['city'],
                transport=form.cleaned_data['transport'],
            )
            login(request, user, backend='auth_system.backends.EmailBackend')
            return redirect("courier_home")

    return render(request, "courier_register.html", {"form": form})


def courier_login_page(request):
    if request.user.is_authenticated:
        return redirect(
            "courier_home"
            if getattr(request.user, 'courier_profile', None)
            else "home"
        )

    form = CourierAuthenticationForm(request=request)
    if request.method == "POST":
        form = CourierAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not getattr(user, 'courier_profile', None):
                form.add_error(None, "Цей обліковий запис не належить кур'єру.")
            else:
                login(request, user, backend='auth_system.backends.EmailBackend')
                return redirect("courier_home")

    return render(request, "courier_login.html", {"form": form})


def login_page(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.user.is_authenticated:
        return redirect(next_url if _is_safe_redirect(request, next_url) else "home")

    form = EmailAuthenticationForm()
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='auth_system.backends.EmailBackend')
            return redirect(next_url if _is_safe_redirect(request, next_url) else "home")

    return render(request, template_name="login.html", context={
        "form": form,
        "next": next_url,
    })


def _is_safe_redirect(request, url):
    return url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


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
                application = RestaurantApplication.objects.filter(
                    owner=user,
                ).order_by('-created_at').first()
                if application and application.status == 'pending':
                    form.add_error(
                        None,
                        'Ваша заявка ще на розгляді. Увійти до кабінету можна після її схвалення.',
                    )
                elif application and application.status == 'rejected':
                    form.add_error(
                        None,
                        'Вашу заявку відхилено. Зверніться до служби підтримки.',
                    )
                else:
                    form.add_error(None, 'Цей обліковий запис не належить ресторану.')
            else:
                login(request, user, backend='auth_system.backends.EmailBackend')
                return redirect("restaurant_home")

    return render(request, template_name="loginforrrestorant.html", context={"form": form})


@login_required
def restaurant_register_page(request):
    form = RestaurantApplicationForm()
    if request.method == "POST":
        form = RestaurantApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(owner=request.user)
            return render(request, "wait.html", {"application": application})

    return render(request, template_name="registerforrestorant.html", context={"form": form})


@login_required
@require_GET
def restaurant_application_status(request, application_id):
    application = get_object_or_404(
        RestaurantApplication,
        pk=application_id,
        owner=request.user,
    )
    return JsonResponse({
        'status': application.status,
        'status_display': application.get_status_display(),
    })


def logout_page(request):
    logout(request)
    return redirect("home")
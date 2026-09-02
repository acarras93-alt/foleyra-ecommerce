from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LoginForm, RegistrationForm


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:product-list")
    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect("catalog:product-list")
    return render(request, "users/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return redirect("catalog:product-list")
    form = LoginForm(request, request.POST if request.method == "POST" else None)
    next_url = request.GET.get("next", "")
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("catalog:product-list")
    return render(request, "users/login.html", {"form": form, "next": next_url})


@require_POST
def logout(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    auth_logout(request)
    return redirect("catalog:product-list")
